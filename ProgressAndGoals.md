# What we've completed

- **MongoDB with geographic data.**  We have cities, states, and countries in the database. Cities belong to states; states belong to countries. The DB is on PythonAnywhere and can be queried by name, code, or ID. The DB can also be run locally for testing as well.

- **REST API for geography.** We built a Flask API with endpoints to create, read, update, and delete countries, states, and cities (including by state/country). Swagger docs are accessible at `/` when the server is running. Each endpoint also has thorough unit tests.

# Requirements and goals

These are goals we hope to fulfill by the end of the spring semester.

**General**

- Building a data explorer for unemployment rate information by geographic area.
- Users select a state or city and see recent unemployment data for that location.
- Historical unemployment data is shown in a graph format.
    - If time permits, we would also like to build a graphical map interface where you can click different states.

**Frontend**

- The explorer's frontend is built in React.
- A map or list of states; clicking a state shows unemployment for that state and a list of its cities.
- Clicking a city shows unemployment for that city.
- The frontend should be clean and intuitive to use.

**Geography**

- States and cities are stored in the database. Cities belong to states.
- The API exposes this hierarchy (list states, list cities by state, etc.).
    - The two above has already been accomplished in our schema from last semester.
- The explorer lists and navigates this hierarchy (e.g. pick a state, then see its cities).

**Data and API**

- Unemployment data is shown for the selected state or city.
- Data is loaded from BLS [state](https://www.bls.gov/web/laus/laumstrk.htm) and [metro](https://www.bls.gov/web/metro/laummtrk.htm) datasets via an ETL script.
    - We might choose different info to show if we find more interesting/fun datasets. They should still be similarly organized by state/city.
- New API endpoints return unemployment by state and by city (or metro).
- API endpoints have a security layer and DB create/delete/update operations are not accessible to all users.
