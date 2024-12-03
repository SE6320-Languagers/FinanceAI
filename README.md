# FinanceAI
Let's learn to finance with our friend LLM

# Description of LLM
Uses open-webui as our web framework base

Users will be able to easily prompt the online GUI to interact with the model, which gives quick, relevant, and easy-to-understand solutions to their questions. Users will be able to ask for feedback on budgets, loans, long-term investments, and other topics related to personal finance.

We will train the model on finance data related to personal finance education and make it available to the users. We want to ensure that the web interface is user friendly, that we have high accuracy to our models, and that we have relevant solutions. The questions that the user will be able to receive answers to will be related to concepts such as credit cards, credit scores, budgeting, loans, mortgages, investing in stocks, and more. We will inform the user that the LLM is simply providing suggestions and explanations about personal finance and that the user should review all information with a personal financial advisor before taking any actions.

# Helpful Information
NLP code file location: backend/open_webui/utils/misc.py
This code preprocesses the user's query before it is passed to the model (Ollama LLM). It contains techniques such as tokenization, lemmatization, named entity recognition, information retrieval, sentiment analysis, and text classification. After these techniques have been applied, the final response is passed to the model.
Dataset file location: training/dataset/dataset-classification.json
This data contains JSON objects with parameters for phrase (personal finance-related user question/prompt), tone, category, and advice (model response) to fine-tune the model to answer the user's personal finance queries and aid in the model's response generation. It also contains helpful facts that can be retrieved (information retrieval) to prevent hallucinations.

# Data Sources
https://www.kaggle.com/datasets/bukolafatunde/personal-finance
https://huggingface.co/datasets/danielv835/personal_finance_v0.2
https://www.kaggle.com/datasets/belayethossainds/yahoo-finance-industries-dataset
https://www.kaggle.com/datasets/sandhaya4u/august-bank-statement-sandhaya
[Lending Club Loan Dataset 2007_2011 (kaggle.com)](https://www.kaggle.com/datasets/imsparsh/lending-club-loan-dataset-2007-2011)
[Credit Card customers (kaggle.com)](https://www.kaggle.com/datasets/sakshigoyal7/credit-card-customers)
[Lending Club Loan Data (kaggle.com)](https://www.kaggle.com/datasets/adarshsng/lending-club-loan-data-csv)


[![Watch the video](https://img.youtube.com/vi/EVKpHfh_HMg/0.jpg)](https://www.youtube.com/watch?v=EVKpHfh_HMg)
(Click the picture above to watch the video!! ^^)