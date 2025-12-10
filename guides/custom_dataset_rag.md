# Using our own dataset to inform a translation model.

If we have a RAG-supported translation model and our own dataset, we can feed this dataset into the model to help it learn whatever patterns or information lie within it.

Some use cases include:
- Showing it how to translate specific phrases / idioms.
- Showing it how to translate certain names / terms.
- Having it copy the "style" of our dataset.

There are typically two main ways of "feeding" this dataset into a model:
1. Fine-tuning the model with the dataset.
2. Using RAG to retrieve a few similar samples from the dataset for every request and showcase them as examples.

(1) can be done with external tools. The model would typically be trained in a PyTorch environment and then exported to a GGUF, which Mango supports. But actually training the model is a massive pain - it's costly and it takes forever.

<sup>(And we have to suffer through hyperparameter tuning, increased hallucination rates, catastrophic forgetting, GPU spot allocation, memory leaks, dataset filtering, model exporting, the list goes on...)</sup>


(2) is almost fully supported out of the box: Mango has RAG built-in. All we need is our own dataset and a RAG-supported translator model that "places" the retrieved samples somewhere in the input prompt.

The `jam_rag_\<language\>` models support RAG and come pre-installed! Custom translator models can also be configured to use RAG.

## Getting Started

### Step 1. Load the dataset.

Mango expects a RAG dataset to be a JSONL file (JSON objects separated by lines). Here's an example of what it should look like:

```
{"source": "This is the Japanese / whatever source language text to translate!", "target": "And this would be the translated output!"}
{"source": "こんにちは", "target": "Hello"}
```

This file should be placed in the models folder under the path `models/database/rag_input_data.jsonl` - make sure the file name is correct!

In some of my personal tests, well-performing datasets would have around 100 - 10000 items.

### Step 2. Configure a custom GGUF translator to use RAG.

**Skip this step if you're using a pre-installed RAG model.**

[See here on how to create a custom translator.](loading_custom_translator_llms.md)

Once we have a custom translator, we need to modify the input prompt to include the `{{JOIN_EACH_RAG_ENTRY(__SRC__ ... __TGT__)}}` operator. For example, here's a custom user message prompt:

`Translate the Japanese text to English.\n\nExamples:\n\n{{JOIN_EACH_RAG_ENTRY(Translate:\n__SRC__\nOutput:\n__TGT__\n)}}\n\nTranslate:\n{{SOURCE}}\nOutput:\n`

### Step 3. Done!

Now select the RAG-supported translator in the Mango options and try translating with it! The RAG data files will be processed on the first translation call, so expect that to take the longest. But once that's done, the RAG data files never need to be processed again.

Up to **three** similar results will be found and appended to the input prompt. If the translator is capable, it should use the results to generate better translations.