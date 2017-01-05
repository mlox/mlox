# Guidelines for Editors of the mlox rule-base

## Introduction

Editors should do their best to keep the rule-base clean and well-documented.

Mlox is managed using version control software called `git`.  If you are unfamiliar with git, please see [here](https://www.atlassian.com/git/tutorials/what-is-git/) for help.

## Citing sources using (Ref:)

Whenever possible, rules should have a "(Ref: xxx)" comment, were xxx is the source of the information the rule is based on. This is necessary so that people will know how to research a rule if they find that it is incorrect, or if they need more information. The citation can be the name of the Readme for the mod, a URL to a web page or forum posting, or anything else that is useful like that. Example:

(Ref: "Luthors Compass 1.0.zip/ReadMe.txt")

In this case, I put the name of the original mod distribution archive in front of the name of the readme file, since the name is very generic, but in most cases, I would leave off the name of the archive, as it should be understood.


### URL whitespace requirements

Please make sure URLs are surrounded with whitespace:

Good:

(Ref: http://www.uesp.net/wiki/Tes3Mod:Leveled_Lists )

Bad:

(Ref: http://www.uesp.net/wiki/Tes3Mod:Leveled_Lists)

Sometimes rules are quoted on web pages (like forum posts) that automatically link URLs, but don't understand that the parenthesis is not part of the link, so they make a bad link. To prevent this, it helps to have the URLs surrounded with whitespace.

## Rules Sections

Most rules are grouped into "sections", which begin with "@" followed by the section name, and each section corresponds more or less to one "Mod". This is only a convention to help keep order in the file, and to generate some happy statistics.

## Highlighting

When a comment message on a rule begins with exclamation points, that comment will be highlighted in the GUI Messages pane.


`! - blue, for low priority.`

Use low priority for stuff that should be "noticed", but probably have low to nil impact on playing. These would often be things that the user might want to know, depending on their preferences.

`!! - yellow, for medium priority.`

Use medium priority for stuff that could possibly impact the game but is probably not too serious. These things probably should be attended to.

`!!! - red, for most urgent priority.`

Use urgent priority for stuff that could break the mod or game. These things should be fixed.

the `[Requires]` rule will automatically highlight in red.

the `[Conflict]` and `[Patch]` rules will automatically highlight in yellow.
