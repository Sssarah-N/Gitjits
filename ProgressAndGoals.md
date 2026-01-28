# 1. What we've completed

- **MongoDB with geographic data.**  We have cities, states, and countries in the database. Cities belong to states; states belong to countries. The DB is on PythonAnywhere and can be queried by name, code, or ID.  

- **REST API for geography.** We built a Flask API with endpoints to create, read, update, and delete countries, states, and cities (including by state/country). Swagger docs are at `/` when the server is running.  

# Requirements

**General**

- The app is a data explorer for unemployment by geographic area.
- The explorer has a React frontend.
- Users select a state or city and see recent unemployment data for that location.

**Geography**

- States and cities are stored in the database. Cities belong to states.
- The API exposes this hierarchy (list states, list cities by state, etc.).
    - The two above has already been accomplished in our schema from last semester.
- The explorer lists and navigates this hierarchy (e.g. pick a state, then see its cities).

**Data**

- Unemployment data is shown for the selected state or city.
- Data is loaded from BLS [state](https://www.bls.gov/web/laus/laumstrk.htm) and [metro](https://www.bls.gov/web/metro/laummtrk.htm) datasets via an ETL script.
    - We might choose different info to show if we find more interesting/fun datasets. They should still be similarly organized by state/city.
- New API endpoints return unemployment by state and by city (or metro).

**Frontend**

- A map or list of states; clicking a state shows unemployment for that state and a list of its cities.
- Clicking a city shows unemployment for that city.
- The frontend should be clean and intuitive to use.