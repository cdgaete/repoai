
## TODO list

- [ ] Add OpenAI API
- [ ] Add Ollama API
- [ ] Test FireworksAI
- [ ] Improve docker prompt to create good files. Add to the prmpt some details based on the experience. Such as allow volumes to be mounted; add UID to avoid permission issues; etc.
- [ ] Add new creation type: based on a context or other repository summary.
- [ ] Add token count of the current chat. So far it shows the accumulation history of the chats.
- [ ] Start using docker to test code and find errors. Show errors and suggests how to fix it.
- [ ] show link to the resulting product. If docker application, show for example http://localhost:8080, if it is a html file, show the link to the html file. Enable to open the browser in either case.
- [ ] create tool to generate basic data summary, to suggest afterwards to make a report using better approaches or packages.
- [ ] tools to be able to get data from internet, create images based on prompts and add them to the repo.
- [ ] Save configuration to share with others.
- [ ] Generate context templates for generation of projects with slightly different ideas.
- [ ] After several trial and error, ask AI if we have learned something to keep in mind for he future. If we agree, then save to a persistent memory.
- [ ] Prepare strategy of difusion and documentation with diagrams, examples and showcase videos and tutorials.
- [ ] Change frontend to a more fancy interface. React maybe.
- [ ] Show new project structure after agree on a prompt, for confirmation to continue or make corrections to the prompt.
- [ ] Config from file. .env file for single variables, repoai_config.json for dictionaries or lists (list could be converted to a dictionary in the future).
- [ ] Currently tool calls partially implemented. Not tested yet. The approach needs to be reviewed. Maybe model with expert tools should be used. Use_tools() not used in the code yet.