# Business Idea Validator API
Businesses run on ideas. However, a bad idea can kill a business before it even starts.
This AI-powered project (MVP) helps businesses validate their ideas and generate business plans
for ideas that are market worthy.

## Features
* Business Idea Validation.
* AI Chat For Idea Refinement.
* Business Plan Generation. 

## Tools and Technologies
* Python - API Development.
* PostgreSQL - Database Technology.
* OpenAI's API (RAG, Embeddings, Prompt Orchestration) - AI Powered Functionalities.
* Render and Supabase - Deployment.

## How To Setup And Run The Project On Your Local Machine
1. Clone the project from GITHUB using the **git clone --url** command.
2. Ensure you have python and postgresql installed on your local machine and ensure your postgresql is currently running.
3. Run the command: **pip install -r requirements.txt** to install the remaining project dependencies.
4. Rename the **sample.env file** into a **.env file** and provide all the required values.
5. Open up your terminal and run the command: **uvicorn main:app --reload**.
6. Your server should be running successfully. You can start interacting with the API Endpoints at **http://127.0.0.1:8000/docs**.

## Helpful Links
* API URL - https://business-idea-validator-backend.onrender.com
* API Documentation - **{{API URL}}/docs**

## Miscellanous
1. You can get an Open AI Secret key by creating an account on the OpenAI platform at: [OPENAI Platform](https://platform.openai.com)
2. You can get a Triberarc Secret key for sending emails by creating an account on Tribearc at: [Tribearc](https://tribearc.com/)