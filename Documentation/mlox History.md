# Introduction - Why mlox?

mlox runs on a little rule-based engine that takes rules from 2 input files: `mlox_base.txt`, which contains general community knowledge, and `mlox_user.txt` (if you have created one), which you can edit to contain local knowledge of your personal load order situation.
You may completely ignore `mlox_user.txt` if you don't want to be bothered with it. It's main audience will be the "power user".

Why mlox? Well, because getting your load order "sorted" (also in the sense of "working correctly") can be a tedious, error-prone job. So why not automate it?

mlox can help in a variety of situations:
* It's not rare that a user will post on a TES forum asking for load order help, and it is readily apparent that they have not read the Readmes for the mods they are using.
For example, sometimes a Readme will say to activate only one of a set of plugins, but they have inadvertently activated them all.
Then they ask why it's not working.
The answer is simply: "run mlox".

* There's also the situation where a power user with hundreds of mods may want to re-install from scratch, but they have so many mods, they've forgotten about some of the pre-reqs, incompatibilities and orderings.
So they end up making little mistakes during the re-install.
Sadly, this has happened to me:)
With the mlox knowledge base, you don't have to remember these details, you just write a rule and the rule remembers for you.
mlox will not forget.

* If you are a modder, and you are tired of hearing people having the same installation problems over and over again with your mod, or hearing about alleged problems with your mod that are actually known conflicts with other mods, you might consider contributing rules to the mlox rule-base that describe orderings, conflicts, and dependencies for your mod.
Then when people have problems, you can tell them to run mlox.

So mlox is potentially for everybody.

That's the theory. Of course, it will take a lot of work to add rules for the many existing mods.
Currently mlox is aware of many popular mods, but there is still much more work to be done to fill out the rule-base.
If mlox succeeds, it will be due to the effort of many.
No one person could do it all.

mlox works by matching filenames specified in rules against the plugins you actually have installed and active.
If you have merged many plugins with the Construction Set, and no longer use the original plugin filenames, mlox will not know this and will not be able to order them or tell you dependencies for your merged plugins.
Of course, if you like, you can write rules yourself and put them in mlox_user.txt to cover these situations.

# Origins of mlox
mlox is inspired by Random007's [BOSS](https://boss-developers.github.io/) (formerly FCOMhelper) project.
BOSS (Better Oblivion Sorting Software) is truly invaluable for Oblivion, because Oblivion is particularly susceptible to crashing if the load order isn't correct, and some mod projects, notably FCOM, require a very large and complicated load ordering that can be difficult to get right.
After BOSS came along, when people post about Oblivion load order problems, the answer to them simply became: "run BOSS".
Hopefully, mlox will become as useful for Morrowind.

However, mlox takes a different approach in the design than the approach used in BOSS.
BOSS uses a "total order" approach, every plugin in the database knows its ordering relationship with every other plugin, mlox uses a "partial order" approach, the rules specify a minimal set of orderings.
If it does not matter whether 2 plugins are in a particular order, there is no ordering specified for them.

BOSS also sometimes requires a second step: every time you run it, all the plugins it doesn't know about end up at the end of the order and must be re-ordered by hand.
(While BOSS knows about a vast number of mods, you may use some it doesn't know about.
Also, experienced users often have some home-grown plugins and patches which BOSS couldn't know about).
mlox uses your current load order as a set of "pseudo-rules", so plugin orderings that are unknown by the rule-base are filled in by what mlox knows about your current order.
If that's too confusing, I'll put it this way, mlox normally only has one step, and you don't need to do any manual reordering afterwards.
If you don't like the order mlox produces, you can add new rules in the mlox_user.txt, but this only has to be done once, from then on it's all automatic.

Finally, I wanted to have a set of rules that could easily express relationships between plugins:
A depends on B, X conflicts with Y, and so on.
This would require writing a simple rule-base system.

Don't take this explanation of the differences as a negative view of BOSS.
I have used BOSS and it really has been invaluable in setting up a working load order for Oblivion.
There's a lot to be said for the simple approach it takes.
For example, the BOSS rule-base is trivial to understand, while the mlox rule-base in comparison is quite complicated and that can potentially lead to errors and behavior that is not understood.
So you can't really say one approach is better than the other.
I just prefer to be able to write rules to customize my load order, and to be able to express dependencies and conflicts, and these are things that really need a little rule-based engine.
So that's why I wrote mlox.

# More recent (ish) history

Mlox started in 2008 as a single python file.
It stayed that way until 2017 when it was broken up into a python module.
However, it wasn't until 2019 that mlox actually supported standard module rules.

At the same time, Mlox was a python 2 program using WX as its graphical interface until 2017.
It was then transitioned to Python 3.  During the transition, I found it difficult to get WX to install/run correctly on Windows, so moved the UI to using Qt.
In many ways, this is a more flexible approach since it allows for basic HTML based rendering of text, and separates code from layout.

Many small changes were and are being made to bring the program up to modern standards.
However, the one thing that has remained mostly untouched is the rules file format.
