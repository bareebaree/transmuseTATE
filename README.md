# transmuseTATE

This project converts music xml files to REMI tokens, put them in embedding space, and attempt to cluster them by musical characteristics and metadata for musicological analysis.

Initial musical characteristics are only pitch, note placement, and note length. Future iterations will attempt to add more musical characteristics such as dynamics and articulation.

Scripts are called in the following order:
[MusicXML (.mxl) files]
          │
          ▼
   (tokenization to REMI)
      └──> xml_to_remi.py
          │
          ▼
[results/all_remi.jsonl] and metadata
          │
          ▼
    (train tokenizer)
      └──> tokenise_remi.py
          │
          ▼
 [remi_tokenizer.json]
          │
          ▼
 (wrap tokenizer for Huggingface)
      └──> huggingface_wrapper.py
          │
          ▼
 [remi-transformer-tokenizer/]
          │
          ▼
 (tokenize dataset with Huggingface tokenizer)
      └──> prepare_dataset.py
          │
          ▼
[results/tokenized_remi_dataset]
          │
          ▼
 (train BERT model)
      └──> train_model.py
          │
          ▼
    [trained REMI-BERT model]
