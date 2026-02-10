# What we've completed

- **MongoDB with geographic data.**  We have cities, states, and countries in the database. Cities belong to states; states belong to countries. The DB is on PythonAnywhere and can be queried by name, code, or ID. The DB can also be run locally for testing as well.

- **REST API for geography.** We built a Flask API with endpoints to create, read, update, and delete countries, states, and cities (including by state/country). Swagger docs are accessible at `/` when the server is running, [link here](https://gitjits.pythonanywhere.com/). Each endpoint also has thorough unit tests.

- **CI/CD tests.** We implemented GitHub Actions to validate that new changes to the code still pass all of our unit tests.

# Requirements and goals

Our goal for this semester is build a national parks explorer. Users will be able to find national parks in each state, and learn more information about hours, available activities, and more.

We will source national parks data from this [dataset](natl_parks.json). This dataset was pulled from the [National Park Service's API](https://www.nps.gov/subjects/developer/api-documentation.htm#/parks/getPark), and has data on 474 national parks. For simplicity, we plan on working with the downloaded JSON rather than integrating with the API, as this data should not be changing frequently.

These are our goals for the end of the semester. Goals labelled (Want) are things we hope to implement only after finishing the core functionality.

## Frontend

- [ ] The explorer's frontend is built in React.
- [ ] Users are able to select a state from a list
    - [ ] (Want) Users can also select states from a visual map
- [ ] Selecting a state shows a list of all national parks in that state
    - [ ] (Want) National parks are shown on a map using latitude/longitude data
- [ ] Selecting a national park shows detailed info about that park. This includes a description, open hours, contact info, activities available at the park, and other details.
- [ ] (Want) Users can search for a national park by name.
- [ ] (Want) Users can filter parks by activities or other criteria.
- [ ] Frontend components have unit tests.
- [ ] Integration tests verify the full flow (state selection -> park list -> park details).


## Database and API

- [ ] Data is loaded from our [national parks dataset](natl_parks.json) via an ETL script.
- [ ] Park entries are tied to state entries by ID in our existing schema. The API exposes this hierarchy, so the frontend can query for parks by state.
- [ ] New API endpoints are created to interact with the parks table.
- [ ] API endpoints have a security layer and DB create/delete/update operations are not accessible to all users.
