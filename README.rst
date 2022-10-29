
.. -*- coding: utf-8 -*-

====================
Git cherry tri state
====================

*************************************************************************
Suspress false positive and improves Git's cherry way to compare branches
*************************************************************************

.. sectnum::

.. contents:: Summary
   :local:
   :backlinks: entry

The problem
===========

Basic case:

Imagine you have a deployed SW, an active master branch and an old maintenance branch that serves to keep official
support on the deployed version.

Imagine the master branch has deeply diverged from the old branch. Lot of bug fixes have been done. *Some* were
backported to the maintenance branch and there was sometimes conflicts due to deep divergence. But the developer was
intelligent and it always kept stable the original commit title after conflict resolution. So some backports are as is,
and some were adapted.

Then you are asked to release long term support version on maintenance branch. All important fixes must be backported
first. Yes it is bad not to have backported them as they come in...

Questions are:

- How do you check that all fixes are backported ?
- How do you list all commits that were not ported to maintenance branch ? So you could select what to backport before
  releasing.

There are hundreds more commits in the master branch, you can't just have a look at and compare manually. You need an
automated tool.

The *git* answer is ``cherry``:

.. code-block:: bash

    git cherry -v --abbrev maintenance_branch master

This command compares both branches and shows status of commits from the ``master`` branch in the ``maintenance`` one:

*  ``-`` tells that commit is present on ``maintenance`` branch (so in both branches).
*  ``+`` tells that commit isn't in ``maintenance`` branch and is candidate for backporting from ``master`` to that
   branch.

The important thing here is that comparision is done on commit **content**. If commit title isn't the same in both
branches, *cherry* is still able to find it in ``maintenance`` branch anyway, based on commit content only.

What isn't satisfying in this case ?
************************************

Remember that there were some conflicts backporting some fixes. For these commits, *cherry* will report ``+`` status
though it was backported because of commit content differs, due to conflict resolution. We would expect status ``-``.

You can have a look to a concrete example at `Example and comparision with cherry`_ below.

The *git_cherry_tri_state* solution
===================================

*git_cherry_tri_state* is an overlayer to ``git cherry`` that introduces a third intermediate state ``~`` between
``-`` and ``+``:

*  ``~`` tells that the commit is present on both branches but content differs. So it is not candidate for backport.

How it works ?
**************

It relies on the stable commit **title**. *git_cherry_tri_state* runs ``git cherry`` then parses the ``+`` commit list
to compare titles with the maintenance branch. If found, the status turns to ``~``. Telling that it is present but
modified!

Yes that implies you keep the same commit title when backporting but this seems very sane. Don't worry about tracking
ticket numbers in titles, keep reading.

How to use it?
**************

Of course you can use that script in other cases. It is simply about comparing two branches. For example you have a
development branch with a lot of commits and some cherry-picked commits from master and you want to see that cherry
picked commits list. Or you want to see what commits will be kept in top of your master if you rebase your branch onto.

The CLI interface is the same as *cherry* except for the options, meaning that mandatory parameters are given as is to
``cherry``. If not given, the parameter *reference-branch* is defaulted to ``HEAD``.

Have a look to the ``-h`` option. There are few more features than in ``cherry`` which is surprisingly poor in term of
options comparing to other *git* commands:

--strip_title:
    Regexp to filter out a part of commit title strings : so you can filter out issue tracker numbers that may differ
    between branches though title is the same:

    On master::

      [#5435] Fix wrong keep alive message ID

    On the other branch, ticket can be different::

      [#5448] Fix wrong keep alive message ID

    Default configuration will strip the ``[...]`` part.

--output_level:
    Filter output level (status) : Suspresses ``-`` only or ``-`` and ``~`` status from output commit list. So you can
    get the real ``+`` missing commit list only.

Example and comparision with ``cherry``
+++++++++++++++++++++++++++++++++++++++

The present repository has an example so you can test the script behavior. There is a ``fake_master`` branch and
``maintenance_v1`` one, they implement a simple *hello world* program of the basic case described in `The problem`_.
Have a look to trees differences between them (last commit is the younger one).

``fake_master`` has::

    829d4fe [#15] Add comments
    b05df3e [#16] Fix bug string 'hello'
    5302043 [#18] Add functionnality 2
    1c17381 [#20] Fix bug string 'functionality 1'
    104f8da [#22] Fix carriage returns on functionalities

``maintenance_v1`` has::

    c8d4696 [#17] Fix bug string 'hello'
    452c724 [#23] Fix carriage returns on functionalities

Pay attention to issue tracking numbers, they differs between ``fake_master`` and ``maintenance_v1`` for the backported
commits: ``16`` becomes ``17`` and ``22`` becomes ``23``.

Then try to get a list of commit candidates to backport from ``master`` to ``maintenance_v1`` running *cherry* and see
what information *git* can bring to you:

.. code-block:: bash

    $ git cherry -v --abbrev maintenance_v1 fake_master
    + 829d4fe [#15] Add comments
    - b05df3e [#16] Fix bug string 'hello'
    + 5302043 [#18] Add functionnality 2
    + 1c17381 [#20] Fix bug string 'functionality 1'
    + 104f8da [#22] Fix carriage returns on functionalities

Conclusions:

- It tells that one commit has yet been backported to ``maintenance_v1``, the one with ticket number 16 though ticket
  number isn't the same one ! Great, *cherry*. seems intelligent !
- It tells that some commits are not present in ``maintenance_v1``: numbers *15*, *18*, *20* and *22*.
- The *22* commit status is ``+`` though there is a commit on ``maintenance_v1`` branch that seems to bring the same
  added value than the last one on ``fake_master`` : number *23*!

Why? Because there was a conflict during backporting that commit and *cherry* failed to match commits content. So it
displays you that commit isn't present though that added value is! It is a *false positive*. You don't want to backport
that commit again!

Now try *git_cherry_tri_state* instead:

.. code-block:: bash

    $ ./git_cherry-tri-state.py maintenance_v1 fake_master
    + 829d4fe [#15] Add comments
    - b05df3e [#16] Fix bug string 'hello'
    + 5302043 [#18] Add functionnality 2
    + 1c17381 [#20] Fix bug string 'functionality 1'
    ~ 104f8da [#22] Fix carriage returns on functionalities

The *22* commit status is now ``~``. So you are aware that it is present but modified (content differs). Note that it
was not confused by the changing ticket number! See option ``--strip_title``.

Now try ``--output_level`` option set to ``+``:

.. code-block:: bash

    $ ./git_cherry-tri-state.py --output_level + maintenance_v1 fake_master
    + 829d4fe [#15] Add comments
    + 5302043 [#18] Add functionnality 2
    + 1c17381 [#20] Fix bug string 'functionality 1'

Levels under to ``+`` are now filterd out from script output. So ``-`` and ``~`` are no more displayed. You can focus
on commits that really matters without any false positive in the list!

Contributions
=============

Ideas and contributions are very welcome!

Please do not fork without a good reason, but keep federated so every one can enjoy your contributions, like me, first
of all :) .
