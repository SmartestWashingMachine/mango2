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
- [LoRAs can teach models new tricks and knowledge.](#loras-can-teach-models-new-tricks-and-knowledge)
  - [LoRA Rank](#lora-rank)
  - [LoRA Alpha](#lora-alpha)
  - [Rank stabilized LoRA](#rank-stabilized-lora)
  - [LoRA dropout](#lora-dropout)
  - [NEFT noise](#neft-noise)
  - [Apply LoRA to all linear layers](#apply-lora-to-all-linear-layers)
  - [Train the input and output embeddings too](#train-the-input-and-output-embeddings-too)
- [RMSNorm, GeGLU, and other architectural tricks are flaky.](#rmsnorm-geglu-and-other-architectural-tricks-are-flaky)
- [Looking for fast results? Use pre-trained models.](#looking-for-fast-results-use-pre-trained-models)
- [LLMs (decoder-only models) aren't as good as encoder-decoder translation models usually.](#llms-decoder-only-models-arent-as-good-as-encoder-decoder-translation-models-usually)
    - [1. Attention degeneration](#1-attention-degeneration)
    - [2. Poor vocabulary](#2-poor-vocabulary)
  - [But ChatGPT blows a bunch of MT models out of the water!](#but-chatgpt-blows-a-bunch-of-mt-models-out-of-the-water)
- [RoPE can't be swapped into an Absolute Positional MT model without pain.](#rope-cant-be-swapped-into-an-absolute-positional-mt-model-without-pain)
- [Gradient Accumulation is NOT equivalent to Batch Size for datasets of varying sequence lengths.](#gradient-accumulation-is-not-equivalent-to-batch-size-for-datasets-of-varying-sequence-lengths)
    - [In the case of batching...](#in-the-case-of-batching)
    - [In the case of gradient accumulating...](#in-the-case-of-gradient-accumulating)
    - [How can we fix this issue?](#how-can-we-fix-this-issue)
- [Make sure the LM head and tokenized input samples are divisible by 8. Usually.](#make-sure-the-lm-head-and-tokenized-input-samples-are-divisible-by-8-usually)
- [Full/Pure BF16 Training is finnicky.](#fullpure-bf16-training-is-finnicky)
- [Make sure `use_reentrant` is False when freezing input embedding layers while using gradient checkpointing.](#make-sure-use_reentrant-is-false-when-freezing-input-embedding-layers-while-using-gradient-checkpointing)
- [D-FINE is way better than YOLO and DETR.](#d-fine-is-way-better-than-yolo-and-detr)
- [Be careful when using LoRA or other low rank adapters on the input embedding layers.](#be-careful-when-using-lora-or-other-low-rank-adapters-on-the-input-embedding-layers)
- [How to fit a bigger model for full-parameter training on one GPU.](#how-to-fit-a-bigger-model-for-full-parameter-training-on-one-gpu)
  - [1. Gradient Checkpointing](#1-gradient-checkpointing)
  - [2. Reduced Batch Size](#2-reduced-batch-size)
  - [3. Memory Efficient Optimizers](#3-memory-efficient-optimizers)
      - [3.1: Adafactor (without momentum)](#31-adafactor-without-momentum)
      - [3.2: AdamW 8bit bitsandbytes](#32-adamw-8bit-bitsandbytes)
      - [3.3: Adam (NOT AdamW) 8bit TorchAO](#33-adam-not-adamw-8bit-torchao)
      - [3.4: Adam (NOT AdamW) 4bit TorchAO](#34-adam-not-adamw-4bit-torchao)
      - [3.5: AdamW 8/4bit TorchAO (I like AdamW 4bit - my favorite)](#35-adamw-84bit-torchao-i-like-adamw-4bit---my-favorite)
  - [4. torch.compile the model AND loss](#4-torchcompile-the-model-and-loss)
  - [5. Optimized cross entropy loss functions](#5-optimized-cross-entropy-loss-functions)
      - [5.1. Liger Kernel Linear Fused Cross Entropy](#51-liger-kernel-linear-fused-cross-entropy)
      - [5.2 Another Fused Linear Cross Entropy](#52-another-fused-linear-cross-entropy)
  - [6. Reduce the model vocabulary (input and output embedding size).](#6-reduce-the-model-vocabulary-input-and-output-embedding-size)
  - [7. Modify the attention logic if it's unoptimized - maybe it can use SDPA?](#7-modify-the-attention-logic-if-its-unoptimized---maybe-it-can-use-sdpa)
  - [8. Pure BF16 Training.](#8-pure-bf16-training)


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

Just don't. Waking up and seeing your GAN collapsed in the middle of the night is like getting punched in the gut. And this will happen every day.

If your friend tries to trick you into training this "awesome" new GAN they found, walk away. That person is not your friend anymore.

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

## LoRAs can teach models new tricks and knowledge.

It's an uncommon belief that LoRAs can only be used to further guide an already trained model, to "refine" its knowledge rather than have it learn new concepts - that LoRAs can not teach the model anything truly new.

I have no idea where this belief came about but from my experiments this seems totally wrong. I've used LoRAs to teach models new concepts numerous times. Some of my experiments included:

1. Successfully trained a 600 million parameter MT model from scratch using LoRAs (albeit weaker than full finetuning obviously).
2. Finetuned an existing 300 million parameter MT model to use document context (doc2sent).
3. Made image models generate new images of a completely different domain.
4. Finetuned an existing 3 billion parameter MT model to use document context.
5. Tuned LLMs on specific tasks that they definitely would never have seen before (no one/few-shots or anything - just LoRA training).
6. Converted an existing 600 million parameter MT model to use relative rather than absolute positional embeddings (albeit weakly).

LoRAs are just parameters. And like anything in machine learning more parameters means more learning. Scale is king. 

When people say their LoRAs couldn't teach their models anything new, I suspect what's actually happening is that their LoRA setups are too weak or under-parametrized or over-regularized to actually learn anything "complex" with.

So what's a proper LoRA setup? I have no idea - it all depends. In machine learning the only constant is that nothing is constant. But that's probably not what you want to hear, so here's a "safe" (but likely not 100% optimal) starter setup:

### LoRA Rank

Make the rank as high as you can without running out of memory and while still training at an acceptable speed. 

When testing the maximum memory used, make sure that your inputs to the model are exactly at the maximum sequence length or the longest sequence length in your dataset (as training memory increases depending on the longest sequence seen during training). 

So test the LoRA rank at say, 512. Failed? Maybe try 256. Failed again? Try 128.

### LoRA Alpha

Just set it equal to your LoRA rank if you're not sure. Alpha either won't affect the training much or it will completely break the training, so it's easy to know when to adjust it.


### Rank stabilized LoRA

Supposedly RS-LoRA helps larger-rank LoRAs generalize better. I've never *needed* it to make larger-rank LoRAs work, but it usually does help.

Apparently Ada-LoRA can also boost your model even more (and it works with RS-LoRA) - there are a lot of papers cheering for it. I have never tried it so I won't say anything there.

### LoRA dropout

Set it to 0. If overfitting is a big concern get more data or just train for less time. *Some* projects may need dropout but those are very specific cases.

### NEFT noise

This is a fairly new trick which injects noise into the model's embeddings. Ideally this noise helps the models learn to separate each embedding token better, similar to how label smoothing encourages models to form better clusters per embedding token.

However, I've found this noise to brick most of my models when used. Use this with caution - unless you're desperate for that possible 1% boost I would keep this off completely.

### Apply LoRA to all linear layers

The "default" LoRA setups in many libraries only applies LoRA to the attention modules. But a lot of papers report better results by applying LoRA to all linear layers (such as the gated linear units used in certain activations, the FFN blocks, and so on).

My experiments agree with them - plus more LoRAs means more parameters so what's not to like?

### Train the input and output embeddings too

If you've added new tokens to the model's vocabulary this is a no-brainer. But even if not, unfreezing the input and output embeddings will usually give a substantial improvement in whatever metric you're using to evaluate your model. Of course, unfreezing these embeddings will drastically increase the trainable parameter count, and therefore the memory cost as well.

## RMSNorm, GeGLU, and other architectural tricks are flaky.

There are dozens upon dozens of little architectural tweaks that supposedly help transformers converge better.

Sadly they're all pretty flaky:

1. GeGLU instead of ReLU / Swish sometimes gives an improvement. Sometimes it doesn't do anything (well, at least it doesn't hurt...)
2. RMSNorm seems to work better with LLMs. But for moderate-sized models the difference is insignificant. Worse yet, for tiny MT models (100m parameters) it seems to be worse than LayerNorm, and it makes relative-positional tiny MT models explode almost immediately, rather than die a slow death over time.
3. Removing all biases in linear layers sometimes improves generalizatiion. Sometimes not. Weird.
4. ReZero usually does worse than other normalization schemes. Every now and then it does something though.
5. Partial convolutions usually don't do anything - but this is for GANs and you should **never ever ever ever** train a GAN. **DO NOT USE GANS.**

I'm not saying we shouldn't keep tweaking our model - I'm sure there is some magical lego block that will make our models do better for some bizarre reason. But if you want something trained in a reasonable amount of time that won't explode, don't bother with architectural modifications.

If you're looking for more neat tricks, this repository has tons of them:
https://github.com/lucidrains/x-transformers

## Looking for fast results? Use pre-trained models.

If you can use a pre-trained model (that was trained on the same modality as yours i.e: text) to accomplish your task - do it. It doesn't matter if it's for an entirely different textual language, or generates anime images when you want car images, **pre-trained models will generalize much faster.** They almost always do.

(But if it's for a different text language, make sure it can tokenize your desired language texts without unknown tokens popping up)

If you can't use a pre-trained model, at least consider if your model has a "backbone" and if that backbone can be swapped out for a pre-trained model, such as the case of using a pre-trained DINO model as the backbone in DETR.

## LLMs (decoder-only models) aren't as good as encoder-decoder translation models usually.

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

## RoPE can't be swapped into an Absolute Positional MT model without pain.

It's as the title says. There is a recent paper where the authors find that they can swap out absolute positional embeddings (APE) for rotary positional embeddings (RoPE), finetuning it to regain most of the original knowledge.

But in my personal experiments, I've found this to be wonky. Finetuning a 1 billion parameter to use RoPE instead of APE has resulted in it "forgetting" almost everything it knows, and the model often hiccups - placing the translated tokens in a very, *very,* wrong order. The hiccups become even more pronounced as the sentence grows longer, and further tuning did not seem to have much of an effect.

On the other hand, MADLAD uses T5 relative positional embeddings and does just fine, hinting to a few possible conclusions. The ones I suspect are:

1. We cannot swap out APE for RoPE in a pretrained MT model - even further tuning would give little advantage.
2. T5 relative positional embeddings are better than RoPE for MT models.

The authors of the paper I mentioned earlier also found that NoPE (**no** positional embeddings) did awfully. That makes sense - we know positional information is crucial for encoder-decoder MT models. 

What's interesting is that other papers find that NoPE does just fine for decoder-only LLMs, albeit on other non-translation tasks. As far as I know decoder-only NoPE LLMs have not been tested on translation tasks, but it *should* work there too, as NoPE models seem to "learn" a positional embedding of their own.

So why can decoder-only LLMs function without positional embeddings but encoder-decoder models can not?

Could the various tasks and massive data scale be the key to allowing LLMs to learn a positional embedding? 

Could it be some fundamental architectural characteristic to decoder-only LLMs?

Since a decoder in the encoder-decoder and an LLM are pretty similar architecturally except for the cross attention block, the issue - if architectural - may lie in the encoder. 

There are people who believe that the causal mask in the decoder, or the unidirectional nature of the decoder, allows it to learn positional embeddings in spite of NoPE. 

But the encoder is bidirectional. So maybe it prevents or somehow harms the learning of positional knowledge. One interesting idea might be to add some form of positional embedding to the encoder but use NoPE for the decoder.

<sub>Unrelated note: I also remember a paper submitted to an WMT competition where the authors used relative positional embeddings for the encoder, but absolute positional embeddings for the decoder. I wonder why?</sub>

All that said, if encoder-decoder MT models truly need positional information baked in, that might be an interesting insight in of itself. That would mean that we *can* inject priors, or other architectural blocks, or hacks, to strengthen our MT models. Scale might not be king.

## Gradient Accumulation is NOT equivalent to Batch Size for datasets of varying sequence lengths.

Put another way: **Gradient accumulation assumes each sequence is equal. Batching assumes every token is equal.**

Typical gradacc implementations will cause our language models to pay more attention to (or be biased towards) shorter sequences while training.

Why? Let's say we have a language model that tokenizes every word. We're training on two samples:

`I like to drink mountain dew.` (sequence length == 6)

and

`No way!` (sequence length == 2)

#### In the case of batching...

If we batch these samples together *without* gradient accumulation (batch size == 2, gradient accumulation == 1), we will have a batch of (6 + 2) == 8 tokens.

Since we're using a standard language model, our loss function is the cross entropy function, with parameter `reduction=mean`. This parameter will average the loss of each token (ignoring padding tokens), so we get: `(loss of 8 tokens) / (8)`.

#### In the case of gradient accumulating...

Now let's try (batch size == 1, gradient accumulation == 2). We first calculate the first sample loss, still using cross entropy with the mean reduction parameter, giving us: `(loss of 6 tokens) / (6)`.

We then calculate the second sample loss, giving us `(loss of 2 tokens) / (2)`. Since we're using gradient accumulation, we add these two losses together and then average by the number of gradient accumulation steps, totaling: `{[(loss of 6) / (6)] + [(loss of 2) / (2)]} / (grad_acc_steps which is 2, sometimes - depends on the implementation)`. This is usually **not equal** to the batching case above.

As a result, gradient accumulation tends to "upweight" the loss values for shorter sequences, and "downplay" the loss values for longer sequences: The model learns less from longer sequences than is the case for normal batching.

This is only an issue if we have varying sequence lengths in training. If our sequence length stays fixed or constant during training then this issue won't pop up.

#### How can we fix this issue?

If we want to fix this issue... We're in for a bad time.

We can't just divide the loss value each time we calculate it. Most implementations immediately do a `loss.backward()` call after every sample - and we don't know how many tokens we have before iterating through the next samples in our DataSampler / DataLoader / whatever.

The best solution IMO is:

1. Change the cross entropy function to use `reduction=sum`.
2. Remove the code that divides each sample's loss value by the number of gradient accumulation steps.
3. Keep a running count of the number of non-padding tokens while iterating over samples.
4. Before the `optimizer.step()` call and *before gradient clipping* we have to iterate over the model's parameters, and divide any non-None grads by the running count of non-padding tokens.
5. Reset the running count whenever we do the `optimizer.step()` call - obviously after step 4.

Regrettably, this solution will cause any logged loss values to show as being exceedingly high (it won't affect the model though: We're chopping down the gradients directly at step 4). 

Make sure to use some sort of validation metric to keep proper track of the model if using this method. And maybe log the gradient norms too (for sanity checking).

## Make sure the LM head and tokenized input samples are divisible by 8. Usually.

According to the ancient Codex, more formally known as the NVIDIA developer docs, having tensor shapes divisible by 8 or other factors can lead to higher tensor core activation, leading to faster training times. This improvement is more noticeable in the final LM head output, as our model likely has a massive vocabulary.

So if our model has an output vocabulary (and consequently, output embedding size) of `52001`, maybe extend the output vocabulary to `52008`.

Likewise, if we are inputting a sequence of total length `14`, maybe pad it so that it becomes a sequence of length `16`.

It's a bit flaky when and when not a speedup actually occurs, but in my runs I've usually seen slightly faster training times when doing this.

(Also: Do not try to profile the tensor core activation rate manually unless you enjoy pulling your hair out. Just profile or track the general training time instead)

## Full/Pure BF16 Training is finnicky.

Training a model with pure BF16 precision (loaded in bfloat16) can be a headache. My suggestions:

1. Ensure no AMP (automatic mixed precision) code is active on the training script. Most AMP implementations end up creating an additional clone of the model to handle high precision updates, which leads to additional memory cost. Since we're doing full half-precision training this doesn't matter. Make sure AMP is off.
2. Use stochastic rounding. Stochastic rounding made my pure BF16 experiments *much* better (stable). This library is fantastic as it already implements it alongside a 4 bit Adam optimizer: https://github.com/pytorch/ao
3. If using that AO package (you should if memory saving is the goal... why else would you be here?): Keep in mind that package implements both Adam **and** AdamW optimizers. Make sure to use the right one (which is probably AdamW - though it uses more memory than Adam...)
4. Do **not** initialize new layers or weights while the model is loaded in half precision. If you want to expand the model, do it while it's still loaded in full precision, *then* load the newly expanded model in half precision. Failing to do this will usually lead to NaN gradients or weights.
5. Be careful with `torch.compile` - it can sometimes lead to **increased** memory usage with half precision models. Not sure what's going on there...
6. Be careful with custom loss implementations (e.g: certain libraries implementing fused linear cross entropy functions): These implementations sometimes assume that the model is in full precision or AMP and can cause weird errors on full BF16 training.
7. **When finetuning: Only process losses below a certain gradient norm threshold** - Rarely the lower-precision model may receive an update with an extremely large gradient norm (sometimes over 9000!). Gradient clipping stops the model from breaking for good, but it does **not stop the model from "forgetting" a lot of knowledge.** As a hacky fix, I skipped the optimization step (but still zero'd the gradients) if the update gradient norm was above some absurd threshold, and it made the finetuning process much safer and happier. Note that since the start of finetuning/pretraining will almost always have large gradient norms initially, it might be best to add this threshold after the gradients have gone down to a relatively sane number. You might not need this if you follow the step below though...
8. **Increase the Adam epsilon value to a safer value, such as 1e-4.** If you don't, then training on half-precision models will be *much* less stable. Every now and then there will be a **massive** gradient norm spike in the training due to the lower precision in our models and/or Adam itself. There are several discussions online that go into more detail on why this might be the case. The basic gist is that the default epsilon values (1e-7 or 1e-8) can underflow (or just make Adam less stable in general), causing Adam to divide by zero or near zero, which can cause massive gradient norms and catastrophic forgetting (or the model just bricks).

## Make sure `use_reentrant` is False when freezing input embedding layers while using gradient checkpointing.

Title. If use_reentrant is True and this happens, most of the layers that interact with the input embedding layers will fail to receive gradients. No training will be done.

## D-FINE is way better than YOLO and DETR.

D-FINE is a new object detection model inspired by DETR. It blows almost every other detection model out of the water (at least, from my experiments). The library can be a pain to configure, but it's worth it. It's worth it.

https://github.com/Peterande/D-FINE

Unlike a certain other object detection model, D-FINE can adapt to objects of various and abnormal aspect ratios (such as text lines) without having to mess around with the anchor boxes or other priors.

Unlike another certain object detection model, it doesn't kill itself if the learning rate is 0.000001 higher than it should be - it's relatively robust to hyperparameter choice. In fact, the defaults given in the library work wonderfully!

Unlike a certain object detection library, it comes with ready-made scripts to perfectly use it in deployment libraries such as ONNX.

But keep in mind that the ONNX deployment script assumes the images were resized in a certain manner that preserves the aspect ratio, so you probably want to ensure that same or similar resize is done for your training images. These augmentations from Albumentations did the trick for me:
```
    A.LongestMaxSize(1024, interpolation=cv2.INTER_CUBIC),
    A.PadIfNeeded(1024, 1024, border_mode=cv2.BORDER_CONSTANT, value=0),
```

Also you probably want to have an actual progress bar while training, so modify the training loop in the `det_engine.py` file.

I imported TQDM and then modified the line that iterates over the data loader to use the TQDM progress bar:
```
for i, (samples, targets) in tqdm(enumerate(metric_logger.log_every(data_loader, print_freq, header)), total=len(data_loader)):
```

You can also implement gradient accumulation in that very same file if you so wish (but you'll need to adjust the `yaml` config files to account for the additional warmup "steps").

**This model is awesome.** In just 2 epochs it already blew YOLO and DETR out of the water.

Last caveat: The model has a tendency to "overpredict" objects, such as predicting a bounding box around a dog, but then predicting another smaller bounding box around that same dog - one box is right inside the other. Using simple postprocessing methods like NMS can fix that.

## Be careful when using LoRA or other low rank adapters on the input embedding layers.

I experimented with using loRA on the input embeddings themselves (alongside the usual suspects: all attention components, feed forward, LM head). It *kind of worked?*

The models would give a generally good answer or output at times, but at others it would give completely different or nonsensical answers that don't relate to the input at all?

For example, I tuned a T5 model to translate text. I would give it a basic sentence to translate. Instead of the translation, I got a date string? "2024/06/20 15:05:30" (paraphrasing but you get the point)

No, it wasn't a data issue - LoRA training without the embedding layers didn't cause this issue (though it had slightly sadder general performance...)

I'm not saying it's bad to adapt the embedding layers - but please keep an eye open for weird behavior.

NEW NOTE: I "pretrained" another model using LoRA like above, and then tried full parameter finetuning that model afterwards - it failed horrifically: The training would randomly diverge due to **massive** gradient norm spikes every now and then. I tried to rectify this by:

1. Increasing the weight decay. No dice.
2. Lowering the learning rate. Made the breaking spikes less frequent for some time, but the model eventually diverged anyways.
3. Increasing warmup steps. Only delayed the inevitable.
4. Increasing AdamW epsilon. Only delayed the inevitable - but it delayed it much longer than (2) and (3).
5. More aggressive gradient clipping. No dice. (Why does gradient clipping almost always fail me? This was your time to shine, dude...)
6. Ignoring batches where the gradient norm spikes. This "worked". The training remained stable, but over time the gradient norm would spike more and more, so I had to drop more and more batches to keep it stable - not efficient at all.

I will never use LoRA on embeddings again.

## How to fit a bigger model for full-parameter training on one GPU.

We all hate CUDA OOM messages. This is what I usually do to fit bigger models:

### 1. Gradient Checkpointing

(+) Reduced VRAM
(-) Reduced Speed

### 2. Reduced Batch Size

(+) Reduced VRAM
(-) Reduced Speed

If we aren't using BatchNorm, we can usually get the same or similar accuracy or stability of a larger batch size by using gradient accumulation.

Training a Seq2Seq model or not using sequence packing? We can also reduce the token count for each sequence.

### 3. Memory Efficient Optimizers

##### 3.1: Adafactor (without momentum)

(+++) Reduced VRAM (-) Reduced Speed (--) Potentially Lower Quality

##### 3.2: AdamW 8bit bitsandbytes

(++) Reduced VRAM (-) Potentially Lower Quality

https://github.com/bitsandbytes-foundation/bitsandbytes

##### 3.3: Adam (NOT AdamW) 8bit TorchAO

(+++) Reduced VRAM (--) Potentially Lower Quality

https://github.com/pytorch/ao

##### 3.4: Adam (NOT AdamW) 4bit TorchAO

(++++) Reduced VRAM (---) Potentially Lower Quality

##### 3.5: AdamW 8/4bit TorchAO (I like AdamW 4bit - my favorite)

(+ to +++) Reduced VRAM (-) Potentially Lower Quality

### 4. torch.compile the model AND loss

(+ to -) Reduced VRAM (+ to -) Improved/Reduced Speed

### 5. Optimized cross entropy loss functions

(This is only for models that use cross entropy, and has a *much* larger effect on models with a large vocabulary size)

That said, I usually don't use either of these loss functions due to weird bugs and quirks.

##### 5.1. Liger Kernel Linear Fused Cross Entropy

(+) Reduced VRAM (-) Reduced Speed (but it can be faster with a good batch size) (-) Buggy/Conflicting with torch.compile

https://github.com/linkedin/Liger-Kernel

##### 5.2 Another Fused Linear Cross Entropy

(+) Reduced VRAM (-) Buggy

https://github.com/apple/ml-cross-entropy

### 6. Reduce the model vocabulary (input and output embedding size).

We can trim the vocabulary of a pretrained model to make a model faster and more lightweight. 

Most trimming logic will need to be done with custom scripts, but we can reference other implementations to make it a bit easier:

https://github.com/airaria/TextPruner

A trimmed model should also work (mostly well) out of the box if we trimmed it right, without any additional training needed. 

Make sure the trimmed model still works before finetuning, as it is incredibly easy to mess up the trimming logic.

### 7. Modify the attention logic if it's unoptimized - maybe it can use SDPA?

(Small +) Reduced VRAM usage. (-) Will have little effect on a small batch and sequence length.

### 8. Pure BF16 Training.

(++++++) Reduced VRAM usage. (+++) Improved Speed (---) Potentially Lower Quality (---) Moderately unstable.

Please make sure to use stochastic rounding on an optimizer if going this route.
