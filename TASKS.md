# Project goal
A simple cli tool and mcp server for generating and reading markdown documents containing documentation for most relevant software tools and libraries

# Tasks
* create two interfaces for this project: direct cli calls and mcp server. all mcp tools/commands are available as direct cli calls
* update mcp command to instead clone the "smarts" directory into ".smarts" from this repository if it doesn't exist in the current project directory: git@github.com:bayne/smarty-mcfly.git
* add an `install mcp <file>` command that is only available from cli, this will have a required argument for the settings.json file. it will read the file then generate a colored diff that will display to the user using their PAGER with an interactiveprompt asking if they would like to apply the changes.
* add an `install rules <file>` command that is only available from cli, similar flow as the mcp
    * the rule should tell the agent to look at the MANIFEST.md file in `.smarts/` and see if the prompt is relevant to any of the topics. if so then follow the reference in the section for the topic to the directory containing the markdown for the topic
* create a learn command that accepts a topic and a source that gets converted into markdown, updated into the manifest, placed in the correct location:
    * add a command `learn <topic> <subtopic> --url <URL>` to use pandoc to convert the page to markdown and add it to a directory with the topic name
    * add a command `learn <topic> <subtopic> --man <man-page>` use a sensible converter for the man page into markdown
    * add a command `learn <topic> <subtopic> --javadoc <package-id>` use a sensible converter for the javadoc into markdown
    * add a command `learn <topic> <subtopic> --sphinx <package-id>` use a sensible converter for the python docs into markdown
    * add a command `learn <topic> <subtopic> --godoc <module>` use a sensible converter for the go docs into markdown
    * add a command `learn <topic> <subtopic> --rustdoc <create>` use a sensible converter for the rust docs into markdown
