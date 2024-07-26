Observations and Quibbles

- [Tiny machine translation (MT) models on distant language pairs (e.g: Chinese-to-English, Japanese-to-English) fail to train without absolute positional embeddings.](#tiny-machine-translation-mt-models-on-distant-language-pairs-eg-chinese-to-english-japanese-to-english-fail-to-train-without-absolute-positional-embeddings)
- [Tiny MT decoders rely heavily on the encoder embedding output, rather than the layers that transform it.](#tiny-mt-decoders-rely-heavily-on-the-encoder-embedding-output-rather-than-the-layers-that-transform-it)
- [ONNX is witchcraft.](#onnx-is-witchcraft)
- [Hyperparameter tuning? Keep an eye on gradient clipping.](#hyperparameter-tuning-keep-an-eye-on-gradient-clipping)
- [When doing full parameter tuning in RAM and VRAM constrained machines, Adafactor is very nice.](#when-doing-full-parameter-tuning-in-ram-and-vram-constrained-machines-adafactor-is-very-nice)
- [Don't bother with gradient norm clipping if using Adafactor.](#dont-bother-with-gradient-norm-clipping-if-using-adafactor)
- [Bigger is better.](#bigger-is-better)
- [Checkpoint Averaging is a headache, but sometimes it can be okay.](#checkpoint-averaging-is-a-headache-but-sometimes-it-can-be-okay)
- [Using multiple encoders isn't worth the heartache.](#using-multiple-encoders-isnt-worth-the-heartache)
- [Doc2Sent \> Doc2Doc](#doc2sent--doc2doc)
- [Don't try to "prune" the vocabulary of a weight-tied MT model unless you're okay with retraining from scratch.](#dont-try-to-prune-the-vocabulary-of-a-weight-tied-mt-model-unless-youre-okay-with-retraining-from-scratch)
- [If possible, add domain-specific tokens to your MT data.](#if-possible-add-domain-specific-tokens-to-your-mt-data)
- [I'm worried my MT model overfits, what should I do for regularization? What do you think of label smoothing, dropout, and error norm truncation?](#im-worried-my-mt-model-overfits-what-should-i-do-for-regularization-what-do-you-think-of-label-smoothing-dropout-and-error-norm-truncation)
- [Why does my language model sometimes repeats words or phrases over and over?](#why-does-my-language-model-sometimes-repeats-words-or-phrases-over-and-over)
- [Don't train GANs.](#dont-train-gans)
- [By default, TrOCR models are really bad at recognizing text in images with distorted aspect ratios.](#by-default-trocr-models-are-really-bad-at-recognizing-text-in-images-with-distorted-aspect-ratios)
- [NaViT factorized embeddings (and label smoothing) are potato for TrOCR.](#navit-factorized-embeddings-and-label-smoothing-are-potato-for-trocr)
- [Variable-sized Vision Transformers are excellent.](#variable-sized-vision-transformers-are-excellent)
- [YOLO doesn't detect small objects with abnormal aspect ratios (like text lines) well.](#yolo-doesnt-detect-small-objects-with-abnormal-aspect-ratios-like-text-lines-well)
- [For object detection models: Use CIoU over DIoU over GIoU over L1/L2.](#for-object-detection-models-use-ciou-over-diou-over-giou-over-l1l2)
- [MT models can learn to use certain tokens as "garbage cans" or "attention sinks".](#mt-models-can-learn-to-use-certain-tokens-as-garbage-cans-or-attention-sinks)
- [LLMs (decoder-only models) aren't as good encoder-decoder translation models usually.](#llms-decoder-only-models-arent-as-good-encoder-decoder-translation-models-usually)
    - [1. Attention degeneration](#1-attention-degeneration)
    - [2. Poor vocabulary](#2-poor-vocabulary)
  - [But ChatGPT blows a bunch of MT models out of the water!](#but-chatgpt-blows-a-bunch-of-mt-models-out-of-the-water)


## Tiny machine translation (MT) models on distant language pairs (e.g: Chinese-to-English, Japanese-to-English) fail to train without absolute positional embeddings.

There are papers finding that absolute positional embeddings (APE) can be "too strong" and cause overfitting. There are also papers finding that relative positional embeddings (RPE) tend to help language models generalize better, though the results for MT models tend to be more mixed.

I have suspicions that relative positional embeddings is critical for proper named entity translation with contextual sentences in mind. APE-powered models tend to give different representations for sentences if every token in the sentence is shifted by some constant, even if the relative positions stay the same (see the SHAPE paper). This could imperil sentences that are "shifted" due to prior sentences being prepended as context.

I trained a few tiny MT models (~50-200m params), replacing the APE components with RPE components. **All of these models failed to train.** Each model would "break" at some point, culminating in only generating one single token or phrase of tokens, regardless of the input.

To fix this I tried:

- Replacing activation functions (ReLU) with LeakyReLUs. Failed.
- Replacing activation functions with GeLUs. Failed.
- Using B2T normalization instead of post-norm. Failed.
- Using pre-norm instead of post-norm. Failed.
- Tinkering with warmup, learning rate, weight decay. Failed.
- Using different RPE implementations, none coded by myself (in case I made an error). These implementations were: Normal RPE (see Shaw), rotary positions, rotary positions with all qkv rotating (which should allow for absolute positional encoding). I did not try Alibi. **All failed.**
- Using pretrained OPUS models with APE, and replacing the APE with the RPEs listed above. **Still failed.**

I tried training tiny MT models trained with normal RPE **and** APE work okay (see P-Transformer paper), but I suspect that's just because the model is "ignoring" the RPE and still (over?)relying on the APE for most positional information.

It's interesting to note that rotary positional embeddings with all qkv rotating is essentially similar to APE - but it still failed here. Perhaps the issue lies in that APE is added directly to the input embeddings before any attention / FFN tomfoolery, whereas RPE is done in the attention layer itself - it's either "too weak" or "too complicated" for a tiny MT model to understand.

Large (>1b) MT models seem to work fine so far with rotary positional embeddings alone.

## Tiny MT decoders rely heavily on the encoder embedding output, rather than the layers that transform it.

I experimented with SurfaceFusion and a few other papers that allow the decoder to cross attend to the encoder embedding output and *every* encoder layer output (for my tiny MT models, this ranged from 4 - 18).

Each cross attention layer would learn a weight for every encoder output it could attend to.

I found that quite quickly, each decoder layer would place a large weight on the embedding layer output, such as **2.54**, and an incredibly tiny weight on the actual encoder layer outputs themselves, such as **0.00169** or **-0.00051**. The deeper the layer, the less significant the weight.

I tried setting a prior value for each cross attention weight, putting more emphasis on later layers, to no avail. The model would eventually "learn" to rely on the embedding layer and ignore everything else.

As training went on, this disparity would only grow. I suspect that this is partly due to how the gradients work: The embedding layer is transformed in each subsequent layer. This leads to more gradients "flowing" back to the embedding layer.

But this doesn't fully explain why the other layers were getting less and less important.

What if I remove the embedding output from the cross attention? Then cross attention just relies on the very first layer output it sees, and still ignores the rest. Oh boy. In this case I suspect that the model also learns to make the first layer an identity layer, so as to replicate the embedding output.

I also tried other normalization schemes (pre-norm, post-norm). No luck (though this phenomenon took longer to show with post-norm).

Then I thought that the cross attention layer was relying on the APE information encoded in the embedding layer output, so I moved the APE to be right after the embedding is passed to the cross attention. No luck.

Now, why is this so bad? Why do we care if the decoder ignores non-embedding outputs? That's simple. The embedding layer has *zero* contextual information - it transforms each token one-by-one without regard for the other tokens in the sequence. Very bad!

I suspect that SurfaceFusion might lead to better named entity translation though. A token-by-token or less "compositional" translation may be pivotal to better named entity translation.

## ONNX is witchcraft.

The ONNX maintainers are probably some of the smartest people on the planet. Unfortunately, they tend to speak in vague ominous phrases, saying things like "thread pooling", "Lack of IO-binding may lead to significant slowdown even on GPU-loaded models due to tensors constantly transferring between CPU -> <- GPU so you should use OrtValues and pin memory pointers", "Are your memory-mapped tensors contiguous?", "Inter-op CPU spinning may steal worker threads from the WSGI server which may lead to errors due to lack of thread-safety but you can...", "Bicubic interpolation does not work with scale_factor not equal to (1, 1) for outer dimensions but you can calculate size yourself instead!", "U8S8 saturation 20% compared to U8U8 so maybe reduce range?"

There are also a bunch of strange catches, like opset v16 failing to work with some OPUS model variants, so you need to use opset v14. Or the fact that quantization may randomly fail on some hardware, so you may need to quantize per channel, but that can cause errors on other hardware, so you should also reduce range, but that slows down the quantization time significantly, plus quantizing to int8 isn't good on CUDA GPUs, so you need to quantize to fp16, but that fails to work on CPUs, so you need to... You can see where this is going.

If possible, use the Optimum package to handle the witchcraft for you. Or use some other package that pretends ONNX doesn't exist.

## Hyperparameter tuning? Keep an eye on gradient clipping.

Gradient clipping is used to help stabilize training. It's really nice for transformer models.

But to me it's always felt like a "bandaid" fix. I also have a suspicion that it hurts the model when it comes to learning rare tokens, especially with absolute positional embeddings. I've found better results in some cases by increasing the gradient norm clipping value to a much higher value, such as *2.0*, *3.0*, *5.0*, and even *10.0* (for vision tasks).

At the least, if finetuning a model, consider increasing the gradient norm clip threshold - at that point the model is already in a relatively stable state. A few noisy gradients here and there shouldn't brick it.

## When doing full parameter tuning in RAM and VRAM constrained machines, Adafactor is very nice.

AdamW can be too memory heavy for weak machines. AdamW 8bit is a bit better but still too hungry sometimes. AdamW paged 8bit can be better but it really needs a lot of RAM to work. Adam Mini has similar issues to AdamW paged 8bit - it needs a lot of RAM (not to be confused with VRAM).

Deepspeed should be avoided on a single GPU machine if possible - there's too many weird arcane errors that will make you pull your hair out. It also doesn't work on Windows for some bizarre reason, despite being maintained by Microsoft (you really don't want to train on Windows though - just use WSL 2).

Be careful with GaLoRe - it performed fairly well versus full parameter tuning in my case, but more importantly it's incredibly slow.

That leaves Adafactor - and it works well. Just make sure you're using your own external learning rate with it, and consider tuning the update clipping value (not to be confused with gradient clipping) - though leaving it at *1.0* is a "safe" choice.

## Don't bother with gradient norm clipping if using Adafactor.

Adafactor has its own built in update clipping trick - so Adafactor should not be used with gradient norm clipping. You can still add in gradient clipping if you so desire, but it usually just makes the model converge slower.

Supposedly, Adafactor's update clipping trick might actually be better than gradient norm clipping (I haven't bothered testing myself). Some researchers have tried integrating it into Adam with decent results.

## Bigger is better.

Rather than worrying about architectural hacks and tricks, just increase the model size and/or data size. In my opinion, the only time to consider architectural changes in MT is when it allows for another modality (e.g: integrating vision information into a text transformer), or concerns positional information.

## Checkpoint Averaging is a headache, but sometimes it can be okay.

There's a paper that discusses merging models using a fancy method: "Model Soup". It can give you a very tiny boost.

Please don't use Stochastic Weight Averaging - it fails horrifically on most transformer models for some reason, and MT is no exception (at least in my experiments). It works well on some (convolutional) vision models however, such as YOLO.

## Using multiple encoders isn't worth the heartache.

Meh. I tried using two encoders, one of which was used to encode context. It didn't have any effect.

From my own experiments and reading various papers, it seems adding additional encoders just causes the decoder to treat it as a "noise generator", rather than a module that is actually providing information. Not what we want.

## Doc2Sent > Doc2Doc

Doc2Sent is **much** faster during inference. It performs competitively with Doc2Doc in terms of BLEU and COMET. It also works well with streamed inference pipelines. Your users will thank you.

## Don't try to "prune" the vocabulary of a weight-tied MT model unless you're okay with retraining from scratch.

Weight-tied as in the encoder, decoder, and output embedding weights are all shared.

I thought I could prune a large vocab on NLLB for my desired language pairs only, while mapping the weights to ensure no desired token knowledge was "lost". I also added new tokens via mean embedding initialization.

Unfortunately, while "finetuning" the model, it became apparent that the model had to be trained a lot, far too much in fact - it's as if no prior knowledge was retained at all.

## If possible, add domain-specific tokens to your MT data.

If you have some way to distinguish what "domains" each sample in your dataset belongs to, it's probably a good idea to add a special token to make that clear to the model. MT models pick up on this quirk - adding a special token to honorific translations causes the MT to output more honorific-respecting texts (when the token is given). Adding a special token to "high quality" texts can boost the model's COMET score, and so on.

## I'm worried my MT model overfits, what should I do for regularization? What do you think of label smoothing, dropout, and error norm truncation?

Get more data.

## Why does my language model sometimes repeats words or phrases over and over?

There was a paper by Deepmind that goes into this, among some others. Following some of their experiments and some of my own I believe that this happens because the **model is still undertrained.** As the model is trained longer and longer it should almost never repeat itself.

 You can hack a "fix" by tweaking the generation algorithm, such as by forbidding the model from repeating N-grams. But that only treats the symptoms - not the disease. Train the model more.

## Don't train GANs.

Just don't. Waking up and seeing your GAN collapse is like getting punched in the gut. And this will happen every day.

Diffusion models are a headache to learn, but they're less likely to give you nightmares. If speed is an issue consider latent consistency adapters.

## By default, TrOCR models are really bad at recognizing text in images with distorted aspect ratios.

TrOCR encoders usually use some form of ViT feature extractor to convert the input image into a tensor. This feature extractor usually resizes the image into a fixed width and height (such as 224x224, or 384x384). Regrettably, these feature extractors usually assume the image is relatively "square" - having a similar width and height. This is not at all the case when dealing with images containing text lines, as the image is almost always highly rectangular in shape.

The feature extractor takes the input image, square or not, and resizes it to the expected size, causing our rectangular-shaped text line images to be horrifically distorted and usually unreadable. Somehow we can finetune TrOCR models to "learn" what these distorted images really represent, but it's **not very effective.** Simply changing the background color causes the model to hallucinate false text in many cases.

Another way to fix this issue is to resize the image so that its longest side is equal to the expected side (at most), and pad the remaining side(s) with a fixed color, usually black, until it fits the desired width and height for the model. Unfortunately, **this doesn't work well with small TrOCR models** - the models typically fail to "learn" that the padding is just that - padding. Modifying the architecture to physically ignore the padding patches is another idea, but probably unfeasible in practice. This issue probably stems from the attention layer - one interesting research idea might be to add register tokens and see what happens.

Another another way to probably alleviate this issue is to not resize it to the expected size at all - just throw in the native image as is and tune the model to work with images of varying resolution. This is what's done in various ViT models today. Just pad the image to ensure it's divisible by the patch size (typically *16*). **This is very nice, but fails for tiny text lines.**

Another another another way to alleviate this issue for tiny text lines is to resize it to some large image size while maintaining the aspect ratio. Then, we simply pad the other side so that it is divisible by 16. I've found this approach to be on par with the previous one for most images, but fare much better on tiny text line images. **This is the best approach that I've found so far.**

## NaViT factorized embeddings (and label smoothing) are potato for TrOCR.

TrOCR is a fantastic OCR architecture, and I use it quite extensively in numerous projects. Unfortunately, it's a very picky architecture - many things that work in ViT and normal language models just inexplicably fail to work here. There's no real logic to it - it's <del>all trial and error</del> magic.

Factorized / fractional (learned or Fourier) positional embeddings don't work with TrOCR models (200m params) in my experiments. But absolute and relative (interpolated or not) positional embeddings work just fine.

Actually, I lied about relative positional embeddings. It works, but not nearly as well as absolute positional embeddings here.

And don't do label smoothing for TrOCRs. Label smoothing makes the TrOCR model explode. Why? Aliens.

## Variable-sized Vision Transformers are excellent.

Most "old" ViTs used to take in fixed-size image inputs, of size `224x224` or `384x384`. In my experiments, I found that the bigger the input image (or at least, the "closer" it is to its native size), the better the model - training a moderate-sized ViT to take in `512x512` or `512x224` images gave **much better results** than training a `224x224` large ViT with twice or even thrice the parameter count.

## YOLO doesn't detect small objects with abnormal aspect ratios (like text lines) well.

I don't know why this is the case. Some bizarre convolutional receptive field weirdness probably.

If you need to detect bounding boxes or polygons on small objects with abnormal aspect ratios, then consider DETR or RT-DETR - these models are flimsy to train due to their sensitivity to learning rate and other hyperparameters, but have a better ceiling for these kind of objects.

## For object detection models: Use CIoU over DIoU over GIoU over L1/L2.

CIoU is the best loss function I've found that works on pretty much all object detection cases, regardless of the underlying model. But most training libraries still use GIoU which is a bummer. CIoU is not going to make your model *way stronger,* but every bit helps.

## MT models can learn to use certain tokens as "garbage cans" or "attention sinks".

When the MT model generates a basic token such as a quote `"` I've found that cross attention modules don't bother attending to most tokens - instead it "focuses" almost all of its attention on one or two pointless tokens, such as the beginning of sentence (BOS) token.

## LLMs (decoder-only models) aren't as good encoder-decoder translation models usually.

There are exceptions to this observation (see the section at the bottom). But usually if you finetune a 7b LLama and a ~3b encoder-decoder model, the 3b model will win. Even when you finetune the Llama with special translation prompts, to encourage catastrophic forgetting of all other non-translation tasks, it still underperforms.

Why? Dunno. I have two theories, and there are papers that seem to support them (though I can't find them anymore. Rest in peace my beloved HDD):

#### 1. Attention degeneration 

Encoder-decoder models use two attention modules in the decoder.

One for the decoder to attend to its own tokens (the translation) - the **self attention** module.

One for the decoder to attend to the input tokens (the text to translate) along with its own tokens - the **cross attention** module.

In each attention module, attention scores must sum to *1* - the model must learn which tokens to pay attention to or ignore. We could say the model has a maximum "budget" or allowance on what to pay attention to.

Disentangling these attention modules allows the model to separately model attention for both source and translation, which it may so desperately need. It has a budget for its own translation alone, and another separate budget to consider the source along with its translation.

On the other hand, LLMs only have the **self attention** module, but with the source text and the translation text being crammed inside it. So it has to use its budget wisely, balancing that between between its own translation along with the source text. Even though this is a "self attention" module, since it attends to both source and translation it's technically a cross attention module (of course, there's the matter of attention masks, but let's not get into that here).

Some papers like PrefixLM try to rectify this, and there are papers inspired by it that do claim it allows LLMs to be on par with encoder-decoder models.

Of course, we could also claim that this we don't need any fancy attention tricks - just scale up the model! Attention will get bigger and better. And that'd probably be right. But I don't want to serve 70 billion parameter-sized models to my users just for translation purposes. Do you? That sounds like a pain...

#### 2. Poor vocabulary

MT models are obviously built in mind to accomodate various languages, so the model tokenizer and vocabulary is trained on datasets of numerous languages. 

This in turn allows the model to have a shorter sequence length when tokenizing non-English texts. 

Shorter sequences are easier for a model's attention module(s) to work with and usually lead to more fluent outputs.

Most LLM tokenizers and their vocabularies are trained on mainly English datasets, so they will usually have a *much longer* sequence length when dealing with non-English texts.

The solution? Just "finetune" your tokenizer and vocabulary on whatever non-English dataset you have - try to add about *10000* to *20000* tokens from there (and initialize the new token embeddings with the average of the parent tokens previously used to "compose it"). Then just finetune your LLM like normal (if you're using an adapter, make sure you're training the token embeddings and language modeling head). Some papers report average sequence lengths decreasing by a factor of three by adding about *10000* new tokens.

(Also while not related to fluency, shorter sequences will also lead to inference speedups. Your users will love you.)

All that said, LLMs likely have a place in post-editing translations.

### But ChatGPT blows a bunch of MT models out of the water!

Yes, and so do some others. But these models have hundreds of billions of parameters. I'm all for scaling but you and I aren't made out of money. We have to consider the "low parameter" regime - around the 7 billion parameter mark (oh god).
