# VESTIGAS Backend Coding challenge

Welcome! This document describes the specifications for the VESTIGAS backend coding challenge.

Imagine the following scenario:
We want to offer an intelligence product, that fetches data from multiple sources, aggregates it and offers it to our customers.
This allows our customers to gather insights from multiple sources.

For this challenge, we stick to a single source and don't do complicated data transformations.

## General requirements

- Build a microservice/API that demonstrates your ability to work with external APIs, handle easy data transformations and implement your own API.
- You may not be able to solve all tasks in the intended time of 2-3 hours.
- Good ratio between quality and quantity

## Techstack

- Use a modern Python version, ideally 3.10+
- You can use third-party libraries
- You can use an API framework, ideally FastAPI
- Please use docker and provide Dockerfile(s) and docker-compose.yml files to run the application

## Documentation Requirements

- Clear setup instructions (how to install dependencies, how to run tests, how to run the server, etc.)
- You can share the files via a (private) git repository or a zip file
- Add a brief summary of the design choices

## Challenge Description: External API Scraper and Data Store

Your task is to build a microservice that interacts with an external API, stores the fetched data, and provides results through its own API endpoints.

### Core Requirements

#### 1. API Endpoints

- `POST /fetch`

  - Triggers a job to fetch data from an external API of your choice (e.g., JSONPlaceholder (https://jsonplaceholder.typicode.com/))
  - It's totally fine to call just one external endpoint and get that data (e.g. just the JSONPlaceholder posts endpoint (https://jsonplaceholder.typicode.com/posts))
  - Optionally transform the data in some way. This can be as simple as filtering the data.
  - Stores the fetched data locally (in-memory or ideally a database like sqlite)
  - Returns a status of the fetch operation
  - Handles potential errors and returns appropriate status codes

- `GET /data`

  - Retrieves the stored data from local storage / database
  - Implements query parameters for filtering (e.g., `GET /data?user_id=1`)
    - This depends on the data you chose to fetch. Simple filtering is fine. Make sure to document available filter options.
  - Returns data in a consistent JSON format

- Endpoints don't have to implement authentication

#### 2. Error Handling & Resilience

- Implement proper error handling for external API failures
- Return meaningful JSON error responses with appropriate HTTP status codes
- Make sure repeated fetch calls don’t hit the external API too frequently
- Optionally: Use a caching mechanism (in-memory cache or short-lived persistent cache) to not hit the external API too frequently
- Handle edge cases (e.g. invalid input, missing data)

#### 3. Testing

- Write (simple) unit tests for your API

### Bonus Features (Optional)

1. Background Tasks

   - Implement automatic data fetching every X minutes

2. Task Queue

   - Use a task queue for fetching and processing data

### Evaluation Criteria

Your solution will be evaluated based on:

1. Functionality
2. Code quality and organization
3. Error handling and resilience
4. Testing approach
5. Documentation quality
6. Implementation of bonus features (if attempted)
