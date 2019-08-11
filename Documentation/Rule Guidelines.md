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

# How to Read/Write Rules:

## How Rules work

Multiple instances of rules are allowed.

Rules from mlox_user.txt take precedence over those in mlox_base.txt.
The user is encouraged to use mlox_user.txt to customize their load order, while mlox_base.txt serves as a repository of community knowledge about plugin order, conflicts, notes and such.

A rule starts with a label, like "[Order]", and ends when a new rule starts, or at the end of file.

All filename comparisons are caseless, so you do not have to worry about capitalization of plugin names when entering rules.

Comments begin with ';'. When mlox reads rules, comments are first stripped, and then blank lines are ignored.

In mlox_base.txt, most rules are grouped into "sections", which begin with "@" followed by the section name, and each section corresponds more or less to one "Mod". This is only a convention to help keep order in the file, and to generate some happy statistics.

Filenames do not need to be quoted. The parser is smart enough to figure out where the names start and end.

### Filename Expansion

mlox will recognize special characters in filenames used in the rule-base, and expand them into files that exist in your load order.

First, there are 2 special metacharacters that are treated in the canonical fashion: '?' and '*':

 * ? matches any single character
 * \* matches any number of characters

There is also a special construct: <VER> which matches something that looks like a Version number in the filename. This will match the same version number forms used in the [VER] predicate, refer to the documentation of that predicate for more.

Examples:

    plugin-?.esp matches: plugin-A.esp, plugin-3.esp, and so on.
    plugin-*.esp matches: plugin-one.esp plugin-Banana.esp, and so on.
    plugin-<VER>.esp matches: plugin-1.0.esp, plugin-3.3g.esp, and so on.

Note: expanding filenames in rules can be rather CPU intensive, so while they are convenient, it is suggested that filename expansions be used sparingly.

## Ordering Rules
### The Order Rule

The [Order] rule specifies the order of plugins.
(In the following example, plugin-1.esm comes before plugin-2.esp which comes before plugin-N.esp, and so on).
If two orderings conflict, the first one encountered wins. Order conflicts are called "cycles", and an example would be if we have one rule that puts aaa.esp before bbb.esp, and another rule that puts bbb.esp before aaa.esp.
Whenever we encounter a rule that would cause a cycle, it is discarded.

    [Order]
    plugin-1.esm
    plugin-2.esp
    .
    .
    plugin-N.esp

This rule is read: "plugin-1.esm precedes plugin-2.esp which precedes
plugin-N.esp". It means that plugin-1.esm must precede plugin-2.esp
AND plugin-2.esp must precede plugin-N.esp in the load order. This
relationship is transitive, so plugin-1 must also precede plugin-N.

### Customizing your Load Order

For people that want to customize their load order, the [Order] rule is probably all that is needed. Here is a simple example:

Let's say you want to make sure that mlox always puts plugin "Foo.esp" before "Bar.esp".
Just create a simple text file called "mlox_user.txt" in your mlox directory (using Notepad or whatever) containing the following:

    [Order]
    Foo.esp
    Bar.esp

From now on, when you press the mlox update button, mlox will make sure that this is the order for those 2 plugins.

### The NearStart Rule

The [NearStart] rule specifies that one or more plugins should appear as near as possible to the Start of the load order.

    [NearStart]
    plugin-1.esp
    plugin-2.esp
    .
    .
    plugin-N.esp

Normally there will be only one [NearStart] rule, for the main master file, (Morrowind.esm).
It is not a good idea to write lots of [NearStart] rules.
If you think you have to, we should talk.
Use [Order] rules to place plugins in relationship to each other.

### The NearEnd Rule

The [NearEnd] rule specifies that one or more plugins should appear as near as possible to the End of the load order.

    [NearEnd]
    plugin-1.esp
    plugin-2.esp
    .
    .
    plugin-N.esp

Normally only a few plugins will appear in [NearEnd] rules, like "Mashed Lists.esp".
Abuse of the [NearEnd] rule is frowned upon.

Note that "NearEnd" does not mean "put this plugin at the end of the load order".
Its meaning is closer to: move this plugin closer to the end, where possible.
For details on how NearEnd works, see the document: "mlox_guts.txt"

## Warning Rules

Note: Warnings are normally only given for "active" plugins (i.e., any plugin listed in the [Game Files] section of Morrowind.ini).
The set of active plugins is often a subset of all plugins installed in your data directory.
If you wish to see warnings for all installed plugins, use the `mlox.py -a` command.

### Messages

Rules may be accompanied by a text message.
There are 2 styles.
he first style has the message appear in the brackets that surround the name of the rule.
For example:

    [CONFLICT don't use these together] A.esp B.esp

In this style, the message may not contain a right-bracket.
The second style is a block (multi-line) message, in which the message must follow on the line after the rule name, and all message lines must begin with whitespace.
For example:

    [CONFLICT]
      Do not use
      A.esp and B.esp together
    A.esp
    B.esp

If the message contains information that is considered a "spoiler" it can be blacked out with <hide    text</hide     and it's up to the user to select the text to view it.

### Boolean Expressions

The Warning rules are expressed in terms of the Boolean logical operators:
ALL, ANY, NOT.
You can nest mlox's Boolean expressions using brackets "[]".
Here's an example:

    [NOTE "Whee!"] [ALL A.esp [ANY B1.esp B2.esp]]

This rule says to print the message "Whee!" if you have A.esp active in your plugins list, along with any of B1.esp or B2.esp.

The operators have to operate on something, and that something is called a "predicate".
This is the basic mlox predicate:

    A.esp

It simply means the plugin "A.esp" is in your active load order.

We can make more expressions, or compound predicates from the basic predicates and the boolean operators:

    [ALL A.esp B.esp C.esp]

This predicate states that A.esp, B.esp, and C.esp are all active in your load order at the same time.

Expressions can nest, so we could say:

    [ALL A.esp B.esp [ANY C.esp D.esp]]

This means that A.esp, B.esp, and any of C.esp or D.esp are all active in your load order at the same time.

The parser is fairly flexible.
So all of the following variations of the same rule are equivalent:

    [NOTE "Whee!"] [ALL A.esp [ANY B1.esp B2.esp]]

    [NOTE]
     "Whee!"
    [ALL A.esp [ANY B1.esp B2.esp]]

    [NOTE "Whee!"]
    [ALL A.esp
     	 [ANY B1.esp B2.esp]]

    [NOTE "Whee!"]
    [ALL A.esp
         [ANY B1.esp
              B2.esp]]

#### The Desc predicate

The Desc predicate is a special predicate that matches strings in the header of a plugin with regular expressions.

The form is:

    [DESC /regex/ A.esp]

or

    [DESC !/regex/ A.esp]

It must all be on one line.
The regex should be any normal Python regular expression pattern:
http://docs.python.org/library/re.html#re-syntax

This predicate means plugin A.esp exists and the Description field of the plugin header contains the regular expression /regex/.
(If the first slash is preceded by a bang, it means the description string does not match the given regex).
Here's an example:

    [Note]
     uses deprecated AddToLev* see: http://www.uesp.net/wiki/Tes3Mod:Leveled_Lists
    [DESC /v. 1.1109/ Sris_Alchemy_BM.esp]

In this case, the note will only print out if the header of Sris_Alchemy_BM.esp contains the pattern "v. 1.1109".

You can use a [DESC] predicate in any warning rule, just like any other expression.

#### The Size predicate

The Size predicate is a special predicate that matches the filesize of the .

The form is:

    [SIZE ### A.esp]

or

    [SIZE !### A.esp]

Where ### is the size of the file in bytes.
(!### means that the filesize does not match the given number).

The function must all be on one line.

    [Note]
     This file contains some GMSTs that need to be cleaned.
    [SIZE 2476 moons_soulgems.esp]

In this case, the note will only print out if the size of moons_soulgems.esp is 2476 bytes.

You can use a [SIZE] predicate in any warning rule, just like any other expression.

#### The Ver predicate

Syntax: `[VER operator version plugin.esp]`

Where operator is: <, =, > for comparing less than, equal to, or greater than, and version number is something that looks like a version number.

The format can be fairly sloppy. mlox will recognize up to 3 numbers separated by "." or "_" and followed by a possible alpha character.
So all the following are valid version numbers:

    1.2.3a, 1.0, 1, 1a, 1_3a, 77g

The actual regular expression used for matching version numbers is:
`(\d+(?:[_.-]?\d+)*[a-z]?)`

The Ver predicate is a special predicate that first tries to match the version number string stored in the plugin header, and if that fails it tries to match the version number from the plugin filename.
If a version number is found, it can be used in a comparison.

This predicate must all be on one line, like so:

    [VER = 1.0 A.esp]

This predicate means plugin A.esp exists and the discovered version number matches 1.0.
The format does not have to match the original, as both the given version number and the version number of the plugin are converted to a canonical form before comparison.
Here's an example:

    [Note]
     this is an old version, please upgrade
    [VER < 1.2 foo.esp]

This is read: "print the Note if the version of the plugin is less than 1.2".
Note that you don't really need whitespace around the comparison operator, but it is nice for readability.

You can use a [VER] predicate in any warning rule, just like any other expression.

### The Note Rule

Syntax: `[Note optional-message] expr-1 expr-2 ... expr-N`

Alternate Syntax:
    [Note]
     optional multi-line comment
    expr-1
    expr-2
    .
    .
    expr-N

(All the warning rules have a similar longer alternate syntax form as shown here, which is omitted from now on for the brevity's sake).

The [Note] rule prints the given message when any of the following expressions is true.

Here's how to print a message if any of A.esp, B.esp, C.esp are active:

    [Note message] A.esp B.esp C.esp

This could also be expressed in its longer form:

    [Note]
     message
    A.esp
    B.esp
    C.esp

And any of the plugins can actually be a full Boolean expression:

    [Note message]
    [ALL A.esp [NOT X.esp]]
    [ANY B.esp 7.esp]
    [ALL C.esp elephant.esp potato.esp]

Note: from now on, we'll use the abbreviation <expr> to mean any Boolean expression.

The [Note] rule is just a handy general rule that can be used for almost any situation.

### The Requires Rule

Syntax: `[Requires optional-message] expr-1 expr-2`

The [Requires] rule specifies that when the dependant expression (expr-1) is true, that the consequent expression (expr-2) must be true.

This rule is naturally used to express the dependencies often described in mod Readmes.

Here's an example:

    [Requires]
     "Assassins Armory - Arrows.esp" requires the Area Effect Arrows plugin to be present
     (Ref: "Assassin's Armory readme.doc")
    Assassins Armory - Arrows.esp
    [ANY AreaEffectArrows XB Edition.esp
         AreaEffectArrows.esp]

Since there are a couple versions of the AreaEffectArrows plugin, we make an [ANY] expression for them, since we could any of them.
So this rule says: "Assassins Armory - Arrows.esp" requires that either "AreaEffectArrows XB Edition.esp" or "AreaEffectArrows.esp" must be active.
If not, you get a warning and the message.

The bit in the block message that starts with "(Ref:" is just a Convention used to point you to the source of information where the rule was taken from.
It's often the readme for the mod, or a web page.

### The Conflict Rule

Syntax: `[Conflict optional-message] expr-1 expr-2 ... expr-N`

The [Conflict] rule specifies that if any two of the following expressions are true, then we print out the given message indicating a conflict problem.

### The Patch Rule

Syntax: `[Patch optional-message] expr-1 expr-2`

The [Patch] rule specifies a mutual dependency as in the case of a patch plugin that modifies some original plugin(s), or that glues two more plugins together to make them compatible.
We use this rule to say two things:

1. That we wouldn't want the patch without the original it is supposed to patch
2. We wouldn't want the original to go unpatched.

Here's how we can say that one plugin has a patch:

    [Patch message] patch.esp original.esp

Here's how we can say that a glue (compatibility) patch is necessary for two separate plugins:

    [Patch message] glue-patch.esp [ALL original-X.esp original-Y.esp]

It is sometimes the case that one of the original plugins has multiple versions, in which case we could say:

    [Patch message]
    glue-patch.esp
    [ALL original-X.esp
        [ANY original-Y-MW-Only.esp
             original-Y-TB+BM.esp]]

This means that glue-patch.esp will patch together either:
  `original-X.esp AND original-Y-MW-Only.esp`
or
  `original-X.esp AND original-Y-TB+BM.esp`

The [Patch] rule does not recognise the NOT Boolean expression.

You **can not** write a [Patch] rule like this:

    [Patch message]
    original-X-patch.esp
    [ALL original-X.esp
        [NOT original-Y.esp]]

I.e. that original-X-patch.esp should be used when original-X.esp is loaded but should not be used when original-Y.esp is loaded.

Rather than using the [Patch] rule you need to create equivalent pairs of [Conflict] and [Requires] rules instead. Like:

    [Conflict message]
    original-X-patch.esp
    original-Y.esp

    [Requires message]
    original-X-patch.esp
    original-X.esp
