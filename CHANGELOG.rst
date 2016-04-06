
0.7.3
-----

Pull Requests

- (@phracek)        #108, Fixes #107: Detect if file exists or is not empty
  https://github.com/fedora-infra/the-new-hotness/pull/108
- (@ralphbean)      #109, Correct another instance of mis-used six.iteritems().
  https://github.com/fedora-infra/the-new-hotness/pull/109
- (@phracek)        #111, Fixes #110: This does not really fix the problem. Log about attaching is
  https://github.com/fedora-infra/the-new-hotness/pull/111
- (@ralphbean)      #112, This dict expects a 4-tuple everywhere else in the code.
  https://github.com/fedora-infra/the-new-hotness/pull/112
- (@phracek)        #114, Fix #113 Text in bugzilla has to be clear.
  https://github.com/fedora-infra/the-new-hotness/pull/114
- (@ralphbean)      #115, Handle OSError from 'rm'.
  https://github.com/fedora-infra/the-new-hotness/pull/115
- (@phracek)        #118, Check if dir exists before deleting
  https://github.com/fedora-infra/the-new-hotness/pull/118
- (@ralphbean)      #120, Check if rawhide_version == upstream_version first.
  https://github.com/fedora-infra/the-new-hotness/pull/120

Commits

- 71d7b2151 Fixes #107: Detect if file exists or is not empty
  https://github.com/fedora-infra/the-new-hotness/commit/71d7b2151
- 1a88414ea Correct another instance of mis-used six.iteritems().
  https://github.com/fedora-infra/the-new-hotness/commit/1a88414ea
- a99c1fbda Fixes #110: This does not really fix the problem. Log about attaching is valid only in case really attach.
  https://github.com/fedora-infra/the-new-hotness/commit/a99c1fbda
- c6459c2cc This dict expects a 4-tuple everywhere else in the code.
  https://github.com/fedora-infra/the-new-hotness/commit/c6459c2cc
- d7e91ba3f Fix #113 Text in bugzilla has to be clear.
  https://github.com/fedora-infra/the-new-hotness/commit/d7e91ba3f
- 38ee2caf6 Update text once again with feedback from @pnemade.
  https://github.com/fedora-infra/the-new-hotness/commit/38ee2caf6
- 83f524842 Handle OSError from 'rm'.
  https://github.com/fedora-infra/the-new-hotness/commit/83f524842
- 77e30b3a9 Check if dir exists instead.
  https://github.com/fedora-infra/the-new-hotness/commit/77e30b3a9
- 53cbda5df Check if dir exists before deleting
  https://github.com/fedora-infra/the-new-hotness/commit/53cbda5df
- 48bcd0048 Check if rawhide_version == upstream_version first.
  https://github.com/fedora-infra/the-new-hotness/commit/48bcd0048
- 3a2b1b834 .. but do also publish in this case.
  https://github.com/fedora-infra/the-new-hotness/commit/3a2b1b834
A bugfix to the last release which should attach more information to bugs when
rebase-helper fails to bump things.


0.7.2
-----

Pull Requests

- (@phracek)        #106, Fixes #105: Rebase helper logs
  https://github.com/fedora-infra/the-new-hotness/pull/106

Commits

- 4f145e9c1 Fixes #105 Add logs to bugzilla for another analysis.
  https://github.com/fedora-infra/the-new-hotness/commit/4f145e9c1
- 76f432f76 Typo in text which is mentioned in bugzilla
  https://github.com/fedora-infra/the-new-hotness/commit/76f432f76
- 80e174b46 Fix mistake with tuples. iteritems should not be used.
  https://github.com/fedora-infra/the-new-hotness/commit/80e174b46

0.7.1
-----

Pull Requests

- (@ralphbean)      #104, Handle repoquery differently for yum and dnf.
  https://github.com/fedora-infra/the-new-hotness/pull/104

Commits

- 20f9bd6bb When this fails, log more info.
  https://github.com/fedora-infra/the-new-hotness/commit/20f9bd6bb
- 0f3b72e62 Handle repoquery differently for yum and dnf.
  https://github.com/fedora-infra/the-new-hotness/commit/0f3b72e62
This release swaps out usage of 'rpmdev-bumpspec' for the new 'rebase-helper'.
Credit due to Petr Hracek.

0.7.0
-----

Pull Requests

- (@ralphbean)      #90, Allow mappings for npmjs.com as well as npmjs.org.
  https://github.com/fedora-infra/the-new-hotness/pull/90
- (@ralphbean)      #92, Remove bundled (and outdated) openid client code.
  https://github.com/fedora-infra/the-new-hotness/pull/92
- (@ralphbean)      #96, Rewrite topics to handle development mode.
  https://github.com/fedora-infra/the-new-hotness/pull/96
- (@phracek)        #94, Rebase helper integration.
  https://github.com/fedora-infra/the-new-hotness/pull/94
- (@ralphbean)      #101, Remove pkg_manager detection.
  https://github.com/fedora-infra/the-new-hotness/pull/101
- (@ralphbean)      #103, Make this log statement less verbose.
  https://github.com/fedora-infra/the-new-hotness/pull/103

Commits

- f3b595f65 Support YUM and DNF
  https://github.com/fedora-infra/the-new-hotness/commit/f3b595f65
- b5dbf963c Specbump.
  https://github.com/fedora-infra/the-new-hotness/commit/b5dbf963c
- 6a582b6e2 Fix YUM and DNF usage.
  https://github.com/fedora-infra/the-new-hotness/commit/6a582b6e2
- 776c7e1e4 Merge remote-tracking branch 'upstream/develop' into develop
  https://github.com/fedora-infra/the-new-hotness/commit/776c7e1e4
- c075434e7 Allow mappings for npmjs.com as well as npmjs.org.
  https://github.com/fedora-infra/the-new-hotness/commit/c075434e7
- 2692cdaf0 Remove bundled (and outdated) openid client code.
  https://github.com/fedora-infra/the-new-hotness/commit/2692cdaf0
- e4133a36f Fix some usage of OpenIdBaseClient where we need more flexibility.
  https://github.com/fedora-infra/the-new-hotness/commit/e4133a36f
- 065a7bc46 Typofix.
  https://github.com/fedora-infra/the-new-hotness/commit/065a7bc46
- 4cfa9c93e Add some nice warnings for debugging.
  https://github.com/fedora-infra/the-new-hotness/commit/4cfa9c93e
- b89e56625 Rebase-helper integration
  https://github.com/fedora-infra/the-new-hotness/commit/b89e56625
- 763ee55c2 Iterate over build_logs
  https://github.com/fedora-infra/the-new-hotness/commit/763ee55c2
- 656b62373 Return back trigger.
  https://github.com/fedora-infra/the-new-hotness/commit/656b62373
- 326758e87 Return reference as not list. In case of failure return logs
  https://github.com/fedora-infra/the-new-hotness/commit/326758e87
- d3805d300 Rewrite topics to handle development mode.
  https://github.com/fedora-infra/the-new-hotness/commit/d3805d300
- 311eb4e96 (,,Ő ｘ Ő,,)
  https://github.com/fedora-infra/the-new-hotness/commit/311eb4e96
- b39f1b102 rebase-helper split
  https://github.com/fedora-infra/the-new-hotness/commit/b39f1b102
- 8f182e912 rebase-helper split
  https://github.com/fedora-infra/the-new-hotness/commit/8f182e912
- 71f41582e Merge branch 'rebase-helper' of github.com:phracek/the-new-hotness into rebase-helper
  https://github.com/fedora-infra/the-new-hotness/commit/71f41582e
- 8f374fc95 rebase-helper returns logs and packages after finishing scratch build.
  https://github.com/fedora-infra/the-new-hotness/commit/8f374fc95
- 64d34e815 Final commit with rebase-helper implementation
  https://github.com/fedora-infra/the-new-hotness/commit/64d34e815
- a48c0daf4 Move this outside the try/except block.
  https://github.com/fedora-infra/the-new-hotness/commit/a48c0daf4
- 4ce84bdfc Update config for namespaced pkgs.
  https://github.com/fedora-infra/the-new-hotness/commit/4ce84bdfc
- 77886e530 Remove pkg_manager detection.
  https://github.com/fedora-infra/the-new-hotness/commit/77886e530
- ee7f33504 Not https here.
  https://github.com/fedora-infra/the-new-hotness/commit/ee7f33504
- 75e90b743 Make this log statement less verbose.
  https://github.com/fedora-infra/the-new-hotness/commit/75e90b743
- dbe3d62e5 Promote this log statement to an exception.
  https://github.com/fedora-infra/the-new-hotness/commit/dbe3d62e5
- 218049a7f New version requires rebase-helper
  https://github.com/fedora-infra/the-new-hotness/commit/218049a7f

0.6.4
-----

Pull Requests

- (@pypingou)       #81, When sending a comment to bugzilla add a link to the project in anitya
  https://github.com/fedora-infra/the-new-hotness/pull/81
- (@ralphbean)      #86, Fix release-monitoring.org html scraping.
  https://github.com/fedora-infra/the-new-hotness/pull/86

Commits

- d900b9de9 Specbump.
  https://github.com/fedora-infra/the-new-hotness/commit/d900b9de9
- a8903fa06 When sending a comment to bugzilla add a link to the project in anitya
  https://github.com/fedora-infra/the-new-hotness/commit/a8903fa06
- 47c5f9d55 Fix release-monitoring.org html scraping.
  https://github.com/fedora-infra/the-new-hotness/commit/47c5f9d55
- 54c132d60 Look just for the csrf_token field.
  https://github.com/fedora-infra/the-new-hotness/commit/54c132d60

0.6.3
-----

Pull Requests

- (@ralphbean)      #76, Silence this error email.
  https://github.com/fedora-infra/the-new-hotness/pull/76

Commits

- 8f408e041 Specbump.
  https://github.com/fedora-infra/the-new-hotness/commit/8f408e041
- ac2582180 Silence this error email.
  https://github.com/fedora-infra/the-new-hotness/commit/ac2582180

0.6.2
-----

Some bugfixes.

Pull Requests

- (@ralphbean)      #71, Be a little more aggressive with real build comments.
  https://github.com/fedora-infra/the-new-hotness/pull/71
- (@ralphbean)      #75, Don't act on packages that are retired.
  https://github.com/fedora-infra/the-new-hotness/pull/75

Commits

- 6c41c05cb Be a little more aggressive with real build comments.
  https://github.com/fedora-infra/the-new-hotness/commit/6c41c05cb
- 9468c8ee4 Don't act on packages that are retired.
  https://github.com/fedora-infra/the-new-hotness/commit/9468c8ee4

0.6.1
-----

Just some bugfixes.

Pull Requests

- (@ralphbean)      #70, Rename this to match the function definition.
  https://github.com/fedora-infra/the-new-hotness/pull/70

Commits

- dfc2923af Specbump.
  https://github.com/fedora-infra/the-new-hotness/commit/dfc2923af
- 606d666fb Ensure that we have a package name before chasing down review tickets.
  https://github.com/fedora-infra/the-new-hotness/commit/606d666fb
- a2ad60c86 Rename this to match the function definition.
  https://github.com/fedora-infra/the-new-hotness/commit/a2ad60c86

0.6.0
-----

Pull Requests

- (@danc86)         #47, mark patches as such when attaching them in Bugzilla
  https://github.com/fedora-infra/the-new-hotness/pull/47
- (@puiterwijk)     #57, Use the root url to check for logged in state
  https://github.com/fedora-infra/the-new-hotness/pull/57
- (@ralphbean)      #61, Report successful rawhide builds (mostly) once.
  https://github.com/fedora-infra/the-new-hotness/pull/61
- (@ralphbean)      #62, Try twice to find the rawhide version of packages.
  https://github.com/fedora-infra/the-new-hotness/pull/62
- (@ralphbean)      #63, Fix fedpkg sources parsing.
  https://github.com/fedora-infra/the-new-hotness/pull/63
- (@ralphbean)      #64, Follow up on FTBFS bugs.
  https://github.com/fedora-infra/the-new-hotness/pull/64
- (@ralphbean)      #67, Match bugs also in the ASSIGNED state.
  https://github.com/fedora-infra/the-new-hotness/pull/67
- (@ralphbean)      #66, Handle pkgdb.package.update messages.
  https://github.com/fedora-infra/the-new-hotness/pull/66
- (@ralphbean)      #68, Be extra careful with anitya error panels.
  https://github.com/fedora-infra/the-new-hotness/pull/68
- (@ralphbean)      #69, Mention scratch build results in review request tickets.
  https://github.com/fedora-infra/the-new-hotness/pull/69

Commits

- 3fef00949 Specbump.
  https://github.com/fedora-infra/the-new-hotness/commit/3fef00949
- e2a682eeb mark patches as such when attaching them in Bugzilla
  https://github.com/fedora-infra/the-new-hotness/commit/e2a682eeb
- 7cf5ebbe6 Use the root url to check for logged in state
  https://github.com/fedora-infra/the-new-hotness/commit/7cf5ebbe6
- 8ad4b1863 Report successful rawhide builds (mostly) once.
  https://github.com/fedora-infra/the-new-hotness/commit/8ad4b1863
- b24ada416 Save bz username so it can be referenced.
  https://github.com/fedora-infra/the-new-hotness/commit/b24ada416
- cc4b7f4f0 Try twice to find the rawhide version of packages.
  https://github.com/fedora-infra/the-new-hotness/commit/cc4b7f4f0
- 1e8fac332 Fix fedpkg sources parsing.
  https://github.com/fedora-infra/the-new-hotness/commit/1e8fac332
- 4db986c9e Add a method to query for FTBFS bugs.
  https://github.com/fedora-infra/the-new-hotness/commit/4db986c9e
- dc2aa7744 Follow up on FTBFS bugs.
  https://github.com/fedora-infra/the-new-hotness/commit/dc2aa7744
- d6589d7c3 If pkgdb hands us no upstream_url, then bail out.
  https://github.com/fedora-infra/the-new-hotness/commit/d6589d7c3
- 80f4042b2 Silence some BeautifulSoup warnings.
  https://github.com/fedora-infra/the-new-hotness/commit/80f4042b2
- a9c8ffd42 Handle pkgdb.package.update messages.
  https://github.com/fedora-infra/the-new-hotness/commit/a9c8ffd42
- 4648ed3ca Only return open FTBFS bugs.
  https://github.com/fedora-infra/the-new-hotness/commit/4648ed3ca
- a64d7d338 Operate on all open FTBFS bugs we find, not just the first one.
  https://github.com/fedora-infra/the-new-hotness/commit/a64d7d338
- 700925fa3 Match bugs also in the ASSIGNED state.
  https://github.com/fedora-infra/the-new-hotness/commit/700925fa3
- db929f815 pep8
  https://github.com/fedora-infra/the-new-hotness/commit/db929f815
- 493dba976 Update error text.
  https://github.com/fedora-infra/the-new-hotness/commit/493dba976
- 56ea7ae6a Use different anitya API endpoint to query for packages by project.
  https://github.com/fedora-infra/the-new-hotness/commit/56ea7ae6a
- 2249110d6 Add some tests.
  https://github.com/fedora-infra/the-new-hotness/commit/2249110d6
- 427f443d4 Be extra careful with anitya error panels.
  https://github.com/fedora-infra/the-new-hotness/commit/427f443d4
- 1510b7a10 Fix return statement.
  https://github.com/fedora-infra/the-new-hotness/commit/1510b7a10
- 24b51ae61 Merge branch 'develop' of github.com:fedora-infra/the-new-hotness into develop
  https://github.com/fedora-infra/the-new-hotness/commit/24b51ae61
- de2bd6c61 Make ftbfs_bugs plural to indicate that it returns a generator.
  https://github.com/fedora-infra/the-new-hotness/commit/de2bd6c61
- 51fe83dd6 Change the way we compare dist tags so we compare '.fc24' with '.fc24'.
  https://github.com/fedora-infra/the-new-hotness/commit/51fe83dd6
- 65ba74f4b Mention scratch build results in review request tickets.
  https://github.com/fedora-infra/the-new-hotness/commit/65ba74f4b
- 62d10b1b2 Remove changelog header.
  https://github.com/fedora-infra/the-new-hotness/commit/62d10b1b2

0.5.0
-----

- Specbump. `1346ea086 <https://github.com/fedora-infra/the-new-hotness/commit/1346ea086350bc087d05a5a3f1687e4ba40e8ee4>`_
- Use the new is_monitored "nobuild" flag. `441f78430 <https://github.com/fedora-infra/the-new-hotness/commit/441f78430e092590113cb104d56b7e5c90127bab>`_
- Merge pull request #45 from fedora-infra/feature/nobuild `792078d71 <https://github.com/fedora-infra/the-new-hotness/commit/792078d719253609a0bf7f68f88322b2634bf5b6>`_

0.4.1
-----

- Specbump. `fdb2eebea <https://github.com/fedora-infra/the-new-hotness/commit/fdb2eebeab32a8fdd7615adfed8cadd4dace0c7b>`_
- fix GitHub capitalization `812397ca1 <https://github.com/fedora-infra/the-new-hotness/commit/812397ca189fdb91ed5392dbf6c3ebf8e2be91da>`_
- Merge pull request #41 from fedora-infra/feature/github-name `66ece5a1c <https://github.com/fedora-infra/the-new-hotness/commit/66ece5a1c33b5f0ea2b930e33deeb17237dc78f5>`_

0.4.0
-----

- Specbump. `b498c637e <https://github.com/fedora-infra/the-new-hotness/commit/b498c637e7f07fd4d19576fd4730d235117c5ab2>`_
- Suppress some errors from rpmbuild and friends. `b0b7c0c1c <https://github.com/fedora-infra/the-new-hotness/commit/b0b7c0c1c88edda93850c6da16837360f72003e8>`_
- Merge pull request #25 from fedora-infra/feature/suppress-some-errors `a1ba74a63 <https://github.com/fedora-infra/the-new-hotness/commit/a1ba74a63ef49033273288299bcae5533a4c6723>`_
- Note on the default message posted on bugzilla about packaging and legal changes `ba4ef2220 <https://github.com/fedora-infra/the-new-hotness/commit/ba4ef22205bf74419476e28e5570851e64868ea6>`_
- Strip leading v. `4f10baed7 <https://github.com/fedora-infra/the-new-hotness/commit/4f10baed700eee823ff5c0d971fed0b04674f30f>`_
- Merge pull request #27 from fedora-infra/legal_be_nice `6a9566302 <https://github.com/fedora-infra/the-new-hotness/commit/6a9566302246c4703e89139471538f3d2199296d>`_
- Merge pull request #28 from fedora-infra/feature/strip-leading-v `016b0c57e <https://github.com/fedora-infra/the-new-hotness/commit/016b0c57ed4e5d2f7b3c8861a33aa61d68b31b23>`_
- This should actually be cached. `c9853a41c <https://github.com/fedora-infra/the-new-hotness/commit/c9853a41c999e89c74a8d8cbe164715fc5eb9db2>`_
- Merge pull request #30 from fedora-infra/feature/typofix-revert `9913cbea8 <https://github.com/fedora-infra/the-new-hotness/commit/9913cbea816902d328a3ce381916bb2fa51b5cd5>`_
- Try to fix README rendering. `0d7f6ef85 <https://github.com/fedora-infra/the-new-hotness/commit/0d7f6ef8544378a02df6d60a060aa821cd4c5165>`_
- Further fix. `9a213a4c6 <https://github.com/fedora-infra/the-new-hotness/commit/9a213a4c6a5e4e71016c1fa408b4cbc52c671858>`_
- Propagate srpm-creation and koji-kickoff errors to the ticket. `41d187509 <https://github.com/fedora-infra/the-new-hotness/commit/41d187509c43d39f7c9abed7df5d350790ea72e3>`_
- Create and attach patches to bz tickets we file. `daea3b076 <https://github.com/fedora-infra/the-new-hotness/commit/daea3b076b3c483c56c5a3eff7701984a8d349a2>`_
- Use os.path.join. `f058e4800 <https://github.com/fedora-infra/the-new-hotness/commit/f058e48001c051f2b186c689d8888452b10b15f3>`_
- Merge pull request #36 from fedora-infra/feature/patch-creation `f8b314a42 <https://github.com/fedora-infra/the-new-hotness/commit/f8b314a426fed660cf88e2899a17df390871b845>`_
- Compare sum of new and old tarball. `ed32e48b4 <https://github.com/fedora-infra/the-new-hotness/commit/ed32e48b46c9ef9cbd9295728081f649e01edcd2>`_
- Merge pull request #37 from fedora-infra/feature/not-april-1st `6d9b71279 <https://github.com/fedora-infra/the-new-hotness/commit/6d9b712792beabd0ea9855f5bdb0142867fd01c2>`_
- Listen for pkgdb monitoring toggle events. `df8fddd16 <https://github.com/fedora-infra/the-new-hotness/commit/df8fddd16c134bd095dd15b941c274b7382408c2>`_
- Use exceptions to propagate error messages to fedmsg `34dbb2e77 <https://github.com/fedora-infra/the-new-hotness/commit/34dbb2e77c15c3c0d448abc7cdbc57ecff0b810e>`_
- Convert those ValueErrors to AnityaExceptions which just make more sense. `4a4bd1624 <https://github.com/fedora-infra/the-new-hotness/commit/4a4bd162441f38138f38c9bbb45a7368de5da04f>`_
- Merge pull request #38 from fedora-infra/feature/pkgdb-monitor-toggle `02b72faa5 <https://github.com/fedora-infra/the-new-hotness/commit/02b72faa55afc1afe1456a5aa33376ac7a3e24c3>`_
- Handle multiply mapped anitya projects. `a9eba188b <https://github.com/fedora-infra/the-new-hotness/commit/a9eba188b38481dff1517c2808e65d7599cb9e6b>`_
- Demote this error message. `3630273bd <https://github.com/fedora-infra/the-new-hotness/commit/3630273bd8a953941dc9852adf7e8086312330c1>`_
- Handle newly-mapped packages from anitya. `4cef2de3d <https://github.com/fedora-infra/the-new-hotness/commit/4cef2de3d31f49d63974df2e86cc5bf043cc000e>`_
- Merge pull request #39 from fedora-infra/feature/multiply-mapped `dc5342307 <https://github.com/fedora-infra/the-new-hotness/commit/dc534230715e2aa24c150333b65c766f7166c567>`_

0.3.3
-----

- specbump `a3171f209 <https://github.com/fedora-infra/the-new-hotness/commit/a3171f2099e8c99623481e69304f9b9b3cbeb118>`_
- Demote this log statement. `f99f5f5f5 <https://github.com/fedora-infra/the-new-hotness/commit/f99f5f5f5cd3154ff8769c3be7eeb6448682ab41>`_
- Use the kojira repos to get the latest rawhide info. `3b9d136c0 <https://github.com/fedora-infra/the-new-hotness/commit/3b9d136c0c8adf1ee2ea128ff0361b197671a471>`_
- Merge pull request #20 from fedora-infra/feature/kojira `957298475 <https://github.com/fedora-infra/the-new-hotness/commit/957298475e211a79fb5022752c301eb464e96049>`_
- Drop explicit archlist for now. `2c1caf83f <https://github.com/fedora-infra/the-new-hotness/commit/2c1caf83f99161ef2f1d17c50a1d3006d9834ecd>`_
- Generate a nicer changelog for the scratch task srpm. `97b865e4d <https://github.com/fedora-infra/the-new-hotness/commit/97b865e4d5ee426e4caf9da2bced02b5351174fa>`_
- It's not a duck! `4f3009821 <https://github.com/fedora-infra/the-new-hotness/commit/4f30098215cdd24aa7f8b4da3996f524282078d9>`_
- Merge pull request #22 from fedora-infra/feature/nicer-changelog `9e110051f <https://github.com/fedora-infra/the-new-hotness/commit/9e110051f48df51c9c854536fca77b41abc11629>`_
- For github backend, if the homepage is on github, specify the version_url to use `aa996242f <https://github.com/fedora-infra/the-new-hotness/commit/aa996242f3b80edbdc3f8afb38e988aca17505c4>`_
- Merge pull request #24 from fedora-infra/github_info `10d25ebd6 <https://github.com/fedora-infra/the-new-hotness/commit/10d25ebd621fe1184bc5cd29fac8c8d30b5f1c32>`_

0.3.2
-----

- Specbump. `fa0475659 <https://github.com/fedora-infra/the-new-hotness/commit/fa0475659eb797eaa1240d9c7047fea2d819bb09>`_
- Demote this log statement. `75bb86263 <https://github.com/fedora-infra/the-new-hotness/commit/75bb86263d006f089e53fe966c1d5a482748a9a3>`_
- When a command fails, I'd like to know what it was. `5e221b80c <https://github.com/fedora-infra/the-new-hotness/commit/5e221b80ce6c5ac3970ad265abd38266b9e107c6>`_
- Still more information. `66e9f9bfe <https://github.com/fedora-infra/the-new-hotness/commit/66e9f9bfec9d6d151cc5543ed46916a5eb7323a2>`_
- Only followup on rawhide builds. `ca4199e72 <https://github.com/fedora-infra/the-new-hotness/commit/ca4199e72226493a74d67efd4d354d3b69ae3166>`_
- Get rawhide dist tag from pkgdb, not from config. `cd3ce37ff <https://github.com/fedora-infra/the-new-hotness/commit/cd3ce37ff06ecdf506a19168a3386936dbb449bc>`_
- Merge pull request #15 from fedora-infra/feature/only-rawhide-thank-you `232015f36 <https://github.com/fedora-infra/the-new-hotness/commit/232015f36e9f82090ad78c078a8cef4e52aaadbe>`_

0.3.1
-----

- specbump `e39e82db5 <https://github.com/fedora-infra/the-new-hotness/commit/e39e82db5caef2f1844e45bbc4d02d2f316127dd>`_
- Suppress errors. `d669ecfd3 <https://github.com/fedora-infra/the-new-hotness/commit/d669ecfd3b6772b74219ae75be440e4019322596>`_
- Merge pull request #11 from fedora-infra/feature/supress-errors `ef0a32dab <https://github.com/fedora-infra/the-new-hotness/commit/ef0a32dabb342d01bfe1e957b60cf39183bb1d27>`_
- Only followup on bugs that are not already closed. `a78a6e916 <https://github.com/fedora-infra/the-new-hotness/commit/a78a6e9161c8f72377ad0dc4b3d6f61b591e0f79>`_
- Merge pull request #12 from fedora-infra/feature/limited-followup `7b80bcbea <https://github.com/fedora-infra/the-new-hotness/commit/7b80bcbeaab9e966fe7149b5b7581f28e1fa5857>`_

0.3.0
-----

- specbump `3850a8813 <https://github.com/fedora-infra/the-new-hotness/commit/3850a8813204013d9eafa3aa10ff96d8fad26a9b>`_
- Specfile should pull this in now. `c4b81f078 <https://github.com/fedora-infra/the-new-hotness/commit/c4b81f078abdec91ddae1c4187357c30eb0f9708>`_
- Auto add new packages. `536049a7f <https://github.com/fedora-infra/the-new-hotness/commit/536049a7fed5f0302083875b2d1ad58a5de609a3>`_
- Map package if the project already exists. `c4a323851 <https://github.com/fedora-infra/the-new-hotness/commit/c4a3238511405686ccc640d95b18d769b5745727>`_
- Typofix. `6ca7fc20e <https://github.com/fedora-infra/the-new-hotness/commit/6ca7fc20e43a12959a99c3f695c584ef6393814e>`_
- Merge pull request #10 from fedora-infra/feature/auto-add-new-packages `51e6735f7 <https://github.com/fedora-infra/the-new-hotness/commit/51e6735f7472ac214163fbc32b1f3a601daac872>`_

0.2.2
-----

- bumpspec. `bb3a6d1f0 <https://github.com/fedora-infra/the-new-hotness/commit/bb3a6d1f093a2913a0cefbd2c90bf26b842ff6c6>`_
- Typofix. `6dddc60fc <https://github.com/fedora-infra/the-new-hotness/commit/6dddc60fc15150e3547d05d2f12b65ad6b835e6a>`_
- Add a call to fedpkg sources. `645f5e717 <https://github.com/fedora-infra/the-new-hotness/commit/645f5e71705289288d20daf3784e77d824710948>`_
- Merge pull request #7 from fedora-infra/feature/fedpkg-patches `2be36e1bc <https://github.com/fedora-infra/the-new-hotness/commit/2be36e1bc63a8d3458454faafe4dbbef5f07d1aa>`_
- Add some hacking instructions. `692cc10fb <https://github.com/fedora-infra/the-new-hotness/commit/692cc10fb65434e50f85f22226d04ec8fd9df944>`_
- Use the multiple-topics feature from moksha.hub-1.4.4 `82780ac80 <https://github.com/fedora-infra/the-new-hotness/commit/82780ac8017ed9a845a05bb7aee15b2ad350e7dd>`_
- Merge pull request #8 from fedora-infra/feature/multiple-topics `af38b3b2d <https://github.com/fedora-infra/the-new-hotness/commit/af38b3b2dd918f8eca7f1de9d8bb3cf4d9f8f19a>`_
- Reorganize where formatting of followup-text lives. `1bf3448f3 <https://github.com/fedora-infra/the-new-hotness/commit/1bf3448f38d1d29442763ab52a344a8e967da2bf>`_
- Comment on real koji builds, not just scratch ones.  Fixes #4. `0e7f5cc01 <https://github.com/fedora-infra/the-new-hotness/commit/0e7f5cc01ac4411255f30eac3a7108f5577f814a>`_
- Install and initialize fedmsg.meta since we use it here now. `2972bf618 <https://github.com/fedora-infra/the-new-hotness/commit/2972bf618b6a1997d1d0183a7f78bea72393ed93>`_
- Merge pull request #9 from fedora-infra/feature/comment-on-build `a22e051c1 <https://github.com/fedora-infra/the-new-hotness/commit/a22e051c1b3af46565b7a6fd0410d388090087e1>`_

0.2.1
-----

- bumpspec. `f869c2ac9 <https://github.com/fedora-infra/the-new-hotness/commit/f869c2ac964e4223d82f27a01ce355c8b66f8153>`_
- Add forgotten parens. `1325d5484 <https://github.com/fedora-infra/the-new-hotness/commit/1325d5484a8e4284e13c383232e8d7a90d81bdc7>`_

0.2.0
-----

- Specbump. `47c1d6de7 <https://github.com/fedora-infra/the-new-hotness/commit/47c1d6de7eda487c6ffa3dd7208148df2ab09393>`_
- Tell bugzilla not to save cookies or tokens. `effcb613a <https://github.com/fedora-infra/the-new-hotness/commit/effcb613a85841946a945d3a283486465399b461>`_
- Remove dependence on fedpkg. `398135f9e <https://github.com/fedora-infra/the-new-hotness/commit/398135f9e96482653c3542195bcbc663d86a35e5>`_
- Tell koji the fully-qualified path to the srpm. `6761db430 <https://github.com/fedora-infra/the-new-hotness/commit/6761db430f8b9c2d106b310b4cd97aaf6c4e1eee>`_
- We can't send an email every time here. `b86ea985d <https://github.com/fedora-infra/the-new-hotness/commit/b86ea985dcf61496f17e91dfc747dc06e49d011c>`_
- Condense log. `f3938580b <https://github.com/fedora-infra/the-new-hotness/commit/f3938580be3ce974e470baeff2e422d87822e01a>`_
- Add some fedmsg messages in there. `e8290306e <https://github.com/fedora-infra/the-new-hotness/commit/e8290306e4fc5d810415bc7e755410d729604295>`_

0.1.3
-----

- Specfile. `05535eb7c <https://github.com/fedora-infra/the-new-hotness/commit/05535eb7c8304b1303c04a112f48e96550c80951>`_
- Check pkgdb monitoring status before acting. `60bb7b2e2 <https://github.com/fedora-infra/the-new-hotness/commit/60bb7b2e201bab127f8ca2c52c2c7fdbd6590399>`_
- Merge pull request #3 from fedora-infra/feature/check-monitoring `d953d3161 <https://github.com/fedora-infra/the-new-hotness/commit/d953d3161d4f0cb8292ed42ee100f354c1943d6e>`_
- Make the yumconfig configurable. `b8a25f5d9 <https://github.com/fedora-infra/the-new-hotness/commit/b8a25f5d9fe7d5b2f7d8edde699537360643c21a>`_
- Keep repoid. `09ff85afa <https://github.com/fedora-infra/the-new-hotness/commit/09ff85afa0931a926e17207b111a1119df865f38>`_
- Adjust for new/old APIs. `377024ac8 <https://github.com/fedora-infra/the-new-hotness/commit/377024ac81ef4b8c31781958f20eb3fe50e02490>`_
- Require python-sh. `7ceef9e37 <https://github.com/fedora-infra/the-new-hotness/commit/7ceef9e3759c36ef1311dd904abcb811d6db4a60>`_
