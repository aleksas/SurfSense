# Forum Post Retrieval Test Cases (100)

Goal: each query is intentionally narrow and should retrieve a specific forum post from indexed `thread_*.md` docs.

Pass criteria (per case): top retrieved result should include the expected thread file and post ID, and contain the anchor text.

## TC-001
- Query: Find the forum post that mentions "Specifically, I have added systems at AD 3116, CoRoT-15, CoRoT-33, CWW 89, EPIC 201702477, EPIC 212036875, Kepler-486, Kepler-492, KOI-415, KOI-607, KOI-686, KOI-959, NLTT 41135, RIK 72, TOI-503, TOI-569, TOI-1406, WASP-30 and WASP-128.".
- Expected thread file: `thread_18705.md`
- Expected post: `Post #736` (ID `p148270`), author `Post #58`
- Anchor text: "Specifically, I have added systems at AD 3116, CoRoT-15, CoRoT-33, CWW 89, EPIC 201702477, EPIC 212036875, Kepler-486, Kepler-492, KOI-415, KOI-607, KOI-686, KOI-959, NLTT 41135, RIK 72, TOI-503, TOI-569, TOI-1406, WASP-30 and WASP-128."
- Narrowing tokens: `Kepler-492`, `Kepler-486`, `WASP-128.`, `CoRoT-15`

## TC-002
- Query: Find the forum post that mentions "sur un ?norme ?cran dans une grande salle de spectacle =D) Je pense mettre la musique de 2001 : Odyss?e de l'espace =D Merci d'avance et contacter moi si vous le voulez ( punkos91@gmail.com ) punkos".
- Expected thread file: `thread_13392.md`
- Expected post: `Post #1` (ID `p111620`), author `Post #1`
- Anchor text: "sur un ?norme ?cran dans une grande salle de spectacle =D) Je pense mettre la musique de 2001 : Odyss?e de l'espace =D Merci d'avance et contacter moi si vous le voulez ( punkos91@gmail.com ) punkos"
- Narrowing tokens: `contacter`, `punkos91`, `musique`, `punkos`

## TC-003
- Query: Find the forum post that mentions "Mammalian colour-producing collagen arrays are anatomically and mechanistically identical to structures that have evolved convergently in the dermis of many lineages of birds, the tapetum of some mammals and the cornea of some fishes.".
- Expected thread file: `thread_12320.md`
- Expected post: `Post #1` (ID `p103962`), author `Post #14`
- Anchor text: "Mammalian colour-producing collagen arrays are anatomically and mechanistically identical to structures that have evolved convergently in the dermis of many lineages of birds, the tapetum of some mammals and the cornea of some fishes."
- Narrowing tokens: `colour-producing`, `mechanistically`, `convergently`, `anatomically`

## TC-004
- Query: Find the forum post that mentions "We got so many vaccinations (Cholera, Small Pocks, Yellow fever, Typhoid fever , para Typhoid fever, Hepatitis, Polio, Tetanus, Seasonal Flu...) notably during the years of our high-density travelling to exotic locations...".
- Expected thread file: `thread_13834.md`
- Expected post: `Post #13` (ID `p119837`), author `Post #93`
- Anchor text: "We got so many vaccinations (Cholera, Small Pocks, Yellow fever, Typhoid fever , para Typhoid fever, Hepatitis, Polio, Tetanus, Seasonal Flu...) notably during the years of our high-density travelling to exotic locations..."
- Narrowing tokens: `vaccinations`, `high-density`, `Hepatitis`, `Typhoid`

## TC-005
- Query: Find the forum post that mentions "Spero che non avrai troppi problemi nel futuro quando andrai a bere qualche birre.".
- Expected thread file: `thread_13162.md`
- Expected post: `Post #34` (ID `p117034`), author `Post #46`
- Anchor text: "Spero che non avrai troppi problemi nel futuro quando andrai a bere qualche birre."
- Narrowing tokens: `problemi`, `qualche`, `quando`, `futuro`

## TC-006
- Query: Find the forum post that mentions "Established two millenia ago, the Dominion controled hundreds and perhaps even thousands of star system at its height, governing thorough Vorta inter mediaries and enforsing its policies with genetically engineered Jem'Hadar soldiers.".
- Expected thread file: `thread_8165.md`
- Expected post: `Post #1` (ID `p61719`), author `Post #1`
- Anchor text: "Established two millenia ago, the Dominion controled hundreds and perhaps even thousands of star system at its height, governing thorough Vorta inter mediaries and enforsing its policies with genetically engineered Jem'Hadar soldiers."
- Narrowing tokens: `engineered`, `soldiers.`, `enforsing`, `mediaries`

## TC-007
- Query: Find the forum post that mentions "Infatti" row -5 column 1} wait {duration 5.0} print {text "Marte e' molto piu' piccolo della Terra,\n6.794 Km, ma ha molte caratteristiche simili ad essa.".
- Expected thread file: `thread_3845.md`
- Expected post: `Post #39` (ID `p28669`), author `Post #47`
- Anchor text: "Infatti" row -5 column 1} wait {duration 5.0} print {text "Marte e' molto piu' piccolo della Terra,\n6.794 Km, ma ha molte caratteristiche simili ad essa."
- Narrowing tokens: `caratteristiche`, `Infatti`, `piccolo`, `n6.794`

## TC-008
- Query: Find the forum post that mentions ""Der Befehl "nms" ist entweder falsch geschrieben oder konnte nicht gefunden werden." No missing dll, no system related stuff, only not found.".
- Expected thread file: `thread_17054.md`
- Expected post: `Post #18` (ID `p131324`), author `Post #24`
- Anchor text: ""Der Befehl "nms" ist entweder falsch geschrieben oder konnte nicht gefunden werden." No missing dll, no system related stuff, only not found."
- Narrowing tokens: `geschrieben`, `entweder`, `gefunden`, `werden.`

## TC-009
- Query: Find the forum post that mentions "The SST is operated on the island of La Palma by the Institute for Solar Physics in the Spanish Observatorio del Roque de los Muchachos of the Instituto de Astrofísica de Canarias.".
- Expected thread file: `thread_19970.md`
- Expected post: `Post #5` (ID `p146666`), author `Post #18`
- Anchor text: "The SST is operated on the island of La Palma by the Institute for Solar Physics in the Spanish Observatorio del Roque de los Muchachos of the Instituto de Astrofísica de Canarias."
- Narrowing tokens: `Observatorio`, `Canarias.`, `Muchachos`, `Astrof`

## TC-010
- Query: Find the forum post that mentions "All of these are cpp files in /src/celestia/qt qtappwin qtcelestialbrowser qtdeepskybrowser qteventfinder qtsolarsystembrowser xbel The first and last I had to change 'toascii' to 'tolatin1' for string functions in params.".
- Expected thread file: `thread_17579.md`
- Expected post: `Post #21` (ID `p135671`), author `Post #14`
- Anchor text: "All of these are cpp files in /src/celestia/qt qtappwin qtcelestialbrowser qtdeepskybrowser qteventfinder qtsolarsystembrowser xbel The first and last I had to change 'toascii' to 'tolatin1' for string functions in params."
- Narrowing tokens: `qtsolarsystembrowser`, `qtcelestialbrowser`, `qtdeepskybrowser`, `qteventfinder`

## TC-011
- Query: Find the forum post that mentions "Ausserdem darfst Du nicht einfach fehlende files mit 'touch <file>' creieren und auf NULL Inhalt setzen.".
- Expected thread file: `thread_15716.md`
- Expected post: `Post #4` (ID `p121254`), author `Post #4`
- Anchor text: "Ausserdem darfst Du nicht einfach fehlende files mit 'touch <file>' creieren und auf NULL Inhalt setzen."
- Narrowing tokens: `Ausserdem`, `fehlende`, `creieren`, `setzen.`

## TC-012
- Query: Find the forum post that mentions "Si tu pouvais aussi traduire mes posts ?a me permettrait enfin de comprendre de quoi je parle !".
- Expected thread file: `thread_17019.md`
- Expected post: `Post #1` (ID `p131290`), author `Post #4`
- Anchor text: "Si tu pouvais aussi traduire mes posts ?a me permettrait enfin de comprendre de quoi je parle !"
- Narrowing tokens: `permettrait`, `comprendre`, `traduire`, `pouvais`

## TC-013
- Query: Find the forum post that mentions "...I only checked these against the cmod: botsaucspec botsaucx botsaucxioffx enterpriseidglow enterpriseidglowi enterpriseidglowioffx topsaucspec topsaucx topsaucxioffx They all seemed to match up, but then, as I said, I don't really know what I'm looking at.".
- Expected thread file: `thread_17377.md`
- Expected post: `Post #7` (ID `p134122`), author `Post #5`
- Anchor text: "...I only checked these against the cmod: botsaucspec botsaucx botsaucxioffx enterpriseidglow enterpriseidglowi enterpriseidglowioffx topsaucspec topsaucx topsaucxioffx They all seemed to match up, but then, as I said, I don't really know what I'm looking at."
- Narrowing tokens: `enterpriseidglowioffx`, `enterpriseidglowi`, `enterpriseidglow`, `botsaucxioffx`

## TC-014
- Query: Find the forum post that mentions "The nice thing with llvm is that it can take your c++ code and: An easily retargettable code generator, which currently supports X86, X86-64, PowerPC, PowerPC-64, ARM, Thumb, SPARC, Alpha, CellSPU, MIPS, MSP430, SystemZ, and XCore .".
- Expected thread file: `thread_16855.md`
- Expected post: `Post #7` (ID `p130080`), author `Post #9`
- Anchor text: "The nice thing with llvm is that it can take your c++ code and: An easily retargettable code generator, which currently supports X86, X86-64, PowerPC, PowerPC-64, ARM, Thumb, SPARC, Alpha, CellSPU, MIPS, MSP430, SystemZ, and XCore ."
- Narrowing tokens: `retargettable`, `PowerPC-64`, `SystemZ`, `CellSPU`

## TC-015
- Query: Find the forum post that mentions "the eight that are featured are (in order): TOI-2818, TOI-1811, TOI-2145, TOI-2152, TOI-2583, TOI-2587, TOI-2796, and TOI-2803 .".
- Expected thread file: `thread_20233.md`
- Expected post: `Post #216` (ID `p161544`), author `Post #425`
- Anchor text: "the eight that are featured are (in order): TOI-2818, TOI-1811, TOI-2145, TOI-2152, TOI-2583, TOI-2587, TOI-2796, and TOI-2803 ."
- Narrowing tokens: `TOI-2796`, `TOI-2587`, `TOI-2818`, `TOI-2583`

## TC-016
- Query: Find the forum post that mentions "Code: Select all byte : crosstype; uint16 : catalog1; uint64 : catalog1entry uint16 : catalog2; uint64 : catalog2entry byte : checkbyte; This particular one gives 22 byte blocks.".
- Expected thread file: `thread_19521.md`
- Expected post: `Post #320` (ID `p143980`), author `Post #38`
- Anchor text: "Code: Select all byte : crosstype; uint16 : catalog1; uint64 : catalog1entry uint16 : catalog2; uint64 : catalog2entry byte : checkbyte; This particular one gives 22 byte blocks."
- Narrowing tokens: `catalog2entry`, `catalog1entry`, `checkbyte`, `crosstype`

## TC-017
- Query: Find the forum post that mentions "Euhmm dat is als je dus Engels boven Nederlands prefereert Anders zie de reactie van ajtribick".
- Expected thread file: `thread_16510.md`
- Expected post: `Post #3` (ID `p127078`), author `Post #3`
- Anchor text: "Euhmm dat is als je dus Engels boven Nederlands prefereert Anders zie de reactie van ajtribick"
- Narrowing tokens: `prefereert`, `reactie`, `Engels`, `boven`

## TC-018
- Query: Find the forum post that mentions "Harris.# http://physwww.physics.mcmaster.ca/~harris/mwgc.dat# Bibliography: http://physwww.mcmaster.ca/%7Eharris/mwgc.ref# supplemented by diameters <=> 25mu isophote from# Brian A.".
- Expected thread file: `thread_12421.md`
- Expected post: `Post #1` (ID `p103745`), author `Post #1`
- Anchor text: "Harris.# http://physwww.physics.mcmaster.ca/~harris/mwgc.dat# Bibliography: http://physwww.mcmaster.ca/%7Eharris/mwgc.ref# supplemented by diameters <=> 25mu isophote from# Brian A."
- Narrowing tokens: `physwww.physics.mcmaster.ca`, `physwww.mcmaster.ca`, `Bibliography`, `mwgc.ref`

## TC-019
- Query: Find the forum post that mentions "For example, when I enter "m8", the display shows: Code: Select all M81 M84 M87 M80 M82 M85 M88 M8 / NGC 6523 / Lagoon Nebula M83 M86 M89 ...".
- Expected thread file: `thread_4578.md`
- Expected post: `Post #7` (ID `p33108`), author `Post #4`
- Anchor text: "For example, when I enter "m8", the display shows: Code: Select all M81 M84 M87 M80 M82 M85 M88 M8 / NGC 6523 / Lagoon Nebula M83 M86 M89 ..."
- Narrowing tokens: `M86`, `M84`, `M80`, `M89`

## TC-020
- Query: Find the forum post that mentions "geologic map; so the eras, for instance the paleozoic, is subdivided as lPz/mPz/uPz/Pz and thus their relevants plutonic/volcanic/metamorphic rocks' attributes.".
- Expected thread file: `thread_16045.md`
- Expected post: `Post #10` (ID `p125691`), author `Post #24`
- Anchor text: "geologic map; so the eras, for instance the paleozoic, is subdivided as lPz/mPz/uPz/Pz and thus their relevants plutonic/volcanic/metamorphic rocks' attributes."
- Narrowing tokens: `relevants`, `plutonic`, `eras`, `mPz`

## TC-021
- Query: Find the forum post that mentions "### Code Snippets: ``` Object: Sol/VenusRelative: UncheckedStartX=0StartY=25000StartZ=0FOV=45Speed=3View=TopActions (only 1)...Duration=5Distance=30StartMessage="Descend to 30km"Duration=3EndMessage="Done"Duration=3(All other values are defaults) ```".
- Expected thread file: `thread_5025.md`
- Expected post: `Post #12` (ID `p36712`), author `Post #2`
- Anchor text: "### Code Snippets: ``` Object: Sol/VenusRelative: UncheckedStartX=0StartY=25000StartZ=0FOV=45Speed=3View=TopActions (only 1)...Duration=5Distance=30StartMessage="Descend to 30km"Duration=3EndMessage="Done"Duration=3(All other values are defaults) ```"
- Narrowing tokens: `UncheckedStartX`, `VenusRelative`, `StartMessage`, `TopActions`

## TC-022
- Query: Find the forum post that mentions "When the poet Dante Alighieri in the [i]Commedia [/i]find itself within a "selva oscura" the verse is correctly translated in english as "dark wood" because is more the "spleen" in the meaning than the fact that "there weren't lights".".
- Expected thread file: `thread_17217.md`
- Expected post: `Post #8` (ID `p132694`), author `Post #20`
- Anchor text: "When the poet Dante Alighieri in the [i]Commedia [/i]find itself within a "selva oscura" the verse is correctly translated in english as "dark wood" because is more the "spleen" in the meaning than the fact that "there weren't lights"."
- Narrowing tokens: `Alighieri`, `Commedia`, `oscura`, `spleen`

## TC-023
- Query: Find the forum post that mentions "fyr02 wrote: Other moons I could do, let me know Puck (Fictional) Thalassa Naiad Despina Cordelia Mab Cupid Perdita 2009 S 1 Anthe (fictional or not?) Polydeuces Sycorax Caliban Aegir Trinculo Maybe a model for Pan?".
- Expected thread file: `thread_18536.md`
- Expected post: `Post #20` (ID `p151434`), author `Post #41`
- Anchor text: "fyr02 wrote: Other moons I could do, let me know Puck (Fictional) Thalassa Naiad Despina Cordelia Mab Cupid Perdita 2009 S 1 Anthe (fictional or not?) Polydeuces Sycorax Caliban Aegir Trinculo Maybe a model for Pan?"
- Narrowing tokens: `Perdita`, `Cupid`, `Aegir`, `Mab`

## TC-024
- Query: Find the forum post that mentions "la prochaine notice : UTC-TAI = - 35s ### Code Snippets: ``` Une seconde suppl?mentaire sera introduite ?".
- Expected thread file: `thread_16952.md`
- Expected post: `Post #3` (ID `p130228`), author `Post #2`
- Anchor text: "la prochaine notice : UTC-TAI = - 35s ### Code Snippets: ``` Une seconde suppl?mentaire sera introduite ?"
- Narrowing tokens: `introduite`, `mentaire`, `seconde`, `UTC-TAI`

## TC-025
- Query: Find the forum post that mentions "My system: Dell Latitude E6510 laptop CPU: 8GB, 1.6GHz, Core i7 Q720; Win7 Pro, SP1 Graphics: 512MB, Nvidia Quadro NVS 3100M (embedded); Forceware v270.61 Disk: 320GB, 7200RPM, 3Gb/sec SATA, Seagate Momentus ST9320423AS Display: 1920x1080; Celestia r5186 p.s.".
- Expected thread file: `thread_16812.md`
- Expected post: `Post #2` (ID `p129077`), author `Post #2`
- Anchor text: "My system: Dell Latitude E6510 laptop CPU: 8GB, 1.6GHz, Core i7 Q720; Win7 Pro, SP1 Graphics: 512MB, Nvidia Quadro NVS 3100M (embedded); Forceware v270.61 Disk: 320GB, 7200RPM, 3Gb/sec SATA, Seagate Momentus ST9320423AS Display: 1920x1080; Celestia r5186 p.s."
- Narrowing tokens: `ST9320423AS`, `Momentus`, `Seagate`, `v270.61`

## TC-026
- Query: Find the forum post that mentions "I also filled a few holes in the ecology: for instance, I have included guanacos and vicunas, since North America could use an easier medium-sized grasslands prey species than pronghorns, and used to be lousy with camelids, anyway.".
- Expected thread file: `thread_12592.md`
- Expected post: `Post #12` (ID `p111854`), author `Post #25`
- Anchor text: "I also filled a few holes in the ecology: for instance, I have included guanacos and vicunas, since North America could use an easier medium-sized grasslands prey species than pronghorns, and used to be lousy with camelids, anyway."
- Narrowing tokens: `pronghorns`, `grasslands`, `guanacos`, `camelids`

## TC-027
- Query: Find the forum post that mentions "In the Zubrin/Andrews interplanetary ramjet design, they calculated that the drag force d/dt(mv1) equals the mass of the scooped ions collected per second multiplied by the velocity of the scooped ions within the solar system relative to the ramscoop.".
- Expected thread file: `thread_16395.md`
- Expected post: `Post #17` (ID `p126533`), author `Post #35`
- Anchor text: "In the Zubrin/Andrews interplanetary ramjet design, they calculated that the drag force d/dt(mv1) equals the mass of the scooped ions collected per second multiplied by the velocity of the scooped ions within the solar system relative to the ramscoop."
- Narrowing tokens: `ramscoop.`, `scooped`, `Andrews`, `Zubrin`

## TC-028
- Query: Find the forum post that mentions "Theobserver will begin turning toward the body once the start_interpolation time is reached and befully turned when the end_interpolation time is reached.final_tracking cannot be used with tracking or final_orientationdefault: no tracking.".
- Expected thread file: `thread_13933.md`
- Expected post: `Post #3` (ID `p116050`), author `Post #2`
- Anchor text: "Theobserver will begin turning toward the body once the start_interpolation time is reached and befully turned when the end_interpolation time is reached.final_tracking cannot be used with tracking or final_orientationdefault: no tracking."
- Narrowing tokens: `final_orientationdefault`, `reached.final_tracking`, `start_interpolation`, `end_interpolation`

## TC-029
- Query: Find the forum post that mentions "Nodrak & its moon Perios Tas'an Matri Ranlir Ladka'cer Some of these objects will be getting minor moons whenever I get the chance.".
- Expected thread file: `thread_20087.md`
- Expected post: `Post #13` (ID `p153598`), author `Post #60`
- Anchor text: "Nodrak & its moon Perios Tas'an Matri Ranlir Ladka'cer Some of these objects will be getting minor moons whenever I get the chance."
- Narrowing tokens: `Perios`, `Ranlir`, `Nodrak`, `Ladka`

## TC-030
- Query: Find the forum post that mentions "The Maya Milky Way (Wakah Chan) Based in Dresden Codex "Folio 3" The Milky Way itself was much venerated by the Maya.".
- Expected thread file: `thread_10108.md`
- Expected post: `Post #3` (ID `p77141`), author `Post #1`
- Anchor text: "The Maya Milky Way (Wakah Chan) Based in Dresden Codex "Folio 3" The Milky Way itself was much venerated by the Maya."
- Narrowing tokens: `venerated`, `Dresden`, `Codex`, `Folio`

## TC-031
- Query: Find the forum post that mentions "cmake_check_build_system: $(CMAKE_COMMAND) -S$(CMAKE_SOURCE_DIR) -B$(CMAKE_BINARY_DIR) --check-build-system CMakeFiles/Makefile.cmake 0 .PHONY : cmake_check_build_system 9.".
- Expected thread file: `thread_17134.md`
- Expected post: `Post #13` (ID `p149515`), author `Post #63`
- Anchor text: "cmake_check_build_system: $(CMAKE_COMMAND) -S$(CMAKE_SOURCE_DIR) -B$(CMAKE_BINARY_DIR) --check-build-system CMakeFiles/Makefile.cmake 0 .PHONY : cmake_check_build_system 9."
- Narrowing tokens: `cmake_check_build_system`, `check-build-system`, `CMAKE_BINARY_DIR`, `Makefile.cmake`

## TC-032
- Query: Find the forum post that mentions "Les francophones pourront trouver plus facile de lire le fichier "celxmaker-lisezmoi.txt".".
- Expected thread file: `thread_16165.md`
- Expected post: `Post #1` (ID `p124575`), author `Post #1`
- Anchor text: "Les francophones pourront trouver plus facile de lire le fichier "celxmaker-lisezmoi.txt"."
- Narrowing tokens: `celxmaker-lisezmoi.txt`, `francophones`, `pourront`, `trouver`

## TC-033
- Query: Find the forum post that mentions "There can download the JPG textures 150x75 (23.9 KB) 300x150 (49.9 KB) 600x300 (156 KB) 900x450 (331 KB) 1500x750 (850 KB) 3000x1500 (2.72 MB) or 6400x3200 (8.28 MB) 3.".
- Expected thread file: `thread_20412.md`
- Expected post: `Post #1` (ID `p150512`), author `Post #1`
- Anchor text: "There can download the JPG textures 150x75 (23.9 KB) 300x150 (49.9 KB) 600x300 (156 KB) 900x450 (331 KB) 1500x750 (850 KB) 3000x1500 (2.72 MB) or 6400x3200 (8.28 MB) 3."
- Narrowing tokens: `x1500`, `x3200`, `x300`, `x450`

## TC-034
- Query: Find the forum post that mentions "ource=II/224/cadars&recno=9837 ) Rho Cassiopeiae: 450 solar radii ( [https://jumk.de/astronomie/big-stars/rho-cassiopeiae.shtml](https://jumk.de/astronomie/big-stars/rho-cassiopeiae.shtml) ) Thank you.".
- Expected thread file: `thread_17849.md`
- Expected post: `Post #1` (ID `p137266`), author `Post #1`
- Anchor text: "ource=II/224/cadars&recno=9837 ) Rho Cassiopeiae: 450 solar radii ( [https://jumk.de/astronomie/big-stars/rho-cassiopeiae.shtml](https://jumk.de/astronomie/big-stars/rho-cassiopeiae.shtml) ) Thank you."
- Narrowing tokens: `rho-cassiopeiae.shtml`, `astronomie`, `big-stars`, `jumk.de`

## TC-035
- Query: Find the forum post that mentions "*/ #include <iostream> #include <fstream> #include <unistd.h> #include <getopt.h> #include <GL/glew.h> /* * glew.h undefs GLAPI, but never undefs __gl_h_ so osmesa never includes gl.h.".
- Expected thread file: `thread_17012.md`
- Expected post: `Post #3` (ID `p130743`), author `Post #2`
- Anchor text: "*/ #include <iostream> #include <fstream> #include <unistd.h> #include <getopt.h> #include <GL/glew.h> /* * glew.h undefs GLAPI, but never undefs __gl_h_ so osmesa never includes gl.h."
- Narrowing tokens: `glew.h`, `undefs`, `gl_h_`, `GLAPI`

## TC-036
- Query: Find the forum post that mentions "Gǃkúnǁʼhòmdímà would become "G\u01c3k\u00fan\u01c1\u02bch\u00f2md\u00edm\u00e0", but in this case there are problems; Celestia doesn't seem to support all of these characters, and the name appears as "G?kún??hòmdímà".".
- Expected thread file: `thread_20094.md`
- Expected post: `Post #3` (ID `p147465`), author `Post #2`
- Anchor text: "Gǃkúnǁʼhòmdímà would become "G\u01c3k\u00fan\u01c1\u02bch\u00f2md\u00edm\u00e0", but in this case there are problems; Celestia doesn't seem to support all of these characters, and the name appears as "G?kún??hòmdímà"."
- Narrowing tokens: `u00f2md`, `u00edm`, `u02bch`, `u00fan`

## TC-037
- Query: Find the forum post that mentions "I already waded through all those web pages and so i ended up here...Joining the forum...asking a simple question...if anyones out there that write my script please help...i dont ask for much..".
- Expected thread file: `thread_16306.md`
- Expected post: `Post #5` (ID `p125519`), author `Post #3`
- Anchor text: "I already waded through all those web pages and so i ended up here...Joining the forum...asking a simple question...if anyones out there that write my script please help...i dont ask for much.."
- Narrowing tokens: `here...Joining`, `forum...asking`, `question...if`, `help...i`

## TC-038
- Query: Find the forum post that mentions "Chris ### Code Snippets: ``` float r = scale * (abs(plane->normal.x) +abs(plane->normal.y) +abs(plane->normal.z)); ``` ``` float r = scale * plane.normal().cwise().abs().sum(); ``` ``` Vector4f v = v1 + v2; ```".
- Expected thread file: `thread_14025.md`
- Expected post: `Post #1` (ID `p116541`), author `Post #1`
- Anchor text: "Chris ### Code Snippets: ``` float r = scale * (abs(plane->normal.x) +abs(plane->normal.y) +abs(plane->normal.z)); ``` ``` float r = scale * plane.normal().cwise().abs().sum(); ``` ``` Vector4f v = v1 + v2; ```"
- Narrowing tokens: `plane.normal`, `normal.x`, `Vector4f`, `normal.z`

## TC-039
- Query: Find the forum post that mentions "Among those contacted included Steve Burg, Everett Burrell, Eric Chauvin and Kevin Kutchaver.".
- Expected thread file: `thread_16944.md`
- Expected post: `Post #1` (ID `p130178`), author `Post #1`
- Anchor text: "Among those contacted included Steve Burg, Everett Burrell, Eric Chauvin and Kevin Kutchaver."
- Narrowing tokens: `Kutchaver.`, `Everett`, `Burrell`, `Chauvin`

## TC-040
- Query: Find the forum post that mentions "It must be done inside the loop because of local planar accuracynormal = (sonPosR0^sonPosR1):normalize()-- if you want to move freely, just comment this lineviewBodyAbove (normal, sonPos, parPos)endwait()until 1==2 ```".
- Expected thread file: `thread_5000.md`
- Expected post: `Post #1` (ID `p36364`), author `Post #1`
- Anchor text: "It must be done inside the loop because of local planar accuracynormal = (sonPosR0^sonPosR1):normalize()-- if you want to move freely, just comment this lineviewBodyAbove (normal, sonPos, parPos)endwait()until 1==2 ```"
- Narrowing tokens: `lineviewBodyAbove`, `accuracynormal`, `sonPosR1`, `sonPosR0`

## TC-041
- Query: Find the forum post that mentions "Freie Universitaet Berlin and DLR Berlin Vallesmarineris textures from ASU's themis mosaic of the Vallesmarineris.".
- Expected thread file: `thread_18430.md`
- Expected post: `Post #38` (ID `p141284`), author `Post #37`
- Anchor text: "Freie Universitaet Berlin and DLR Berlin Vallesmarineris textures from ASU's themis mosaic of the Vallesmarineris."
- Narrowing tokens: `Vallesmarineris.`, `Vallesmarineris`, `Universitaet`, `Freie`

## TC-042
- Query: Find the forum post that mentions "For exemple : le FC Nantes \u00e9tait meilleur il y a quelques ann\u00e9 es...".
- Expected thread file: `thread_2742.md`
- Expected post: `Post #29` (ID `p49240`), author `Post #31`
- Anchor text: "For exemple : le FC Nantes \u00e9tait meilleur il y a quelques ann\u00e9 es..."
- Narrowing tokens: `u00e9tait`, `meilleur`, `quelques`, `Nantes`

## TC-043
- Query: Find the forum post that mentions "" minutes",10)endendwait(10)touringtime = celestia:getscripttime()returnendfunction tour(systemcentrename,objecttypestoview)systemcentre = celestia:find(systemcentrename)if systemcentre:name() == "?" thencelestia:flash(systemcentrename ..".
- Expected thread file: `thread_20390.md`
- Expected post: `Post #3` (ID `p150343`), author `Post #3`
- Anchor text: "" minutes",10)endendwait(10)touringtime = celestia:getscripttime()returnendfunction tour(systemcentrename,objecttypestoview)systemcentre = celestia:find(systemcentrename)if systemcentre:name() == "?" thencelestia:flash(systemcentrename .."
- Narrowing tokens: `returnendfunction`, `objecttypestoview`, `systemcentrename`, `systemcentre`

## TC-044
- Query: Find the forum post that mentions "The best solution provides the orbital periods, P_c = 3.49 +/- 0.21 years and P_d = 6.86 +/- 0.25 years, and the projected semi-major axes, a_c \sin I_c = 1.9 +/- 0.3 AU and a_d \sin I_d = 2.9 +/- 0.6 AU, for the circumbinary bodies.".
- Expected thread file: `thread_16647.md`
- Expected post: `Post #6` (ID `p131709`), author `Post #19`
- Anchor text: "The best solution provides the orbital periods, P_c = 3.49 +/- 0.21 years and P_d = 6.86 +/- 0.25 years, and the projected semi-major axes, a_c \sin I_c = 1.9 +/- 0.3 AU and a_d \sin I_d = 2.9 +/- 0.6 AU, for the circumbinary bodies."
- Narrowing tokens: `P_d`, `a_d`, `a_c`, `I_d`

## TC-045
- Query: Find the forum post that mentions "The Plutonian Empire was founded in Neuve Pluton, Pluton Island on Earth On January 1st, 2020, in a magically uplifted island in the South Atlantic.".
- Expected thread file: `thread_23095.md`
- Expected post: `Post #1` (ID `p158932`), author `Post #1`
- Anchor text: "The Plutonian Empire was founded in Neuve Pluton, Pluton Island on Earth On January 1st, 2020, in a magically uplifted island in the South Atlantic."
- Narrowing tokens: `Atlantic.`, `magically`, `uplifted`, `Pluton`

## TC-046
- Query: Find the forum post that mentions "G.M., The USS Horatio, amazing model USS Horatio.jpg In the case 'separate model' USS Horatio2.jpg @ tiqhud (BCC) & updated in 3ds.".
- Expected thread file: `thread_17032.md`
- Expected post: `Post #18` (ID `p131839`), author `Post #31`
- Anchor text: "G.M., The USS Horatio, amazing model USS Horatio.jpg In the case 'separate model' USS Horatio2.jpg @ tiqhud (BCC) & updated in 3ds."
- Narrowing tokens: `Horatio2.jpg`, `Horatio.jpg`, `Horatio`, `tiqhud`

## TC-047
- Query: Find the forum post that mentions "& Weilen's CNS3 (revised) catalog at ARICNS (apparently also called CNS4) has FIVE new names in addition to the Gl, GJ and Wo we know: N1 (does not correspond to the unnumbered systems in CNS3p), N2, NV, NH, N3.".
- Expected thread file: `thread_16305.md`
- Expected post: `Post #8` (ID `p125571`), author `Post #14`
- Anchor text: "& Weilen's CNS3 (revised) catalog at ARICNS (apparently also called CNS4) has FIVE new names in addition to the Gl, GJ and Wo we know: N1 (does not correspond to the unnumbered systems in CNS3p), N2, NV, NH, N3."
- Narrowing tokens: `Weilen`, `ARICNS`, `CNS3p`, `CNS4`

## TC-048
- Query: Find the forum post that mentions "GPX-1b is a recently discovered transiting brown dwarf with a mass of 19.7 ± 1.6 MJup, and a radius of 1.47 ± 0.10 RJup, the first sub-stellar object discovered by the GPX ( G alactic P lane e X oplanet) survey!".
- Expected thread file: `thread_20477.md`
- Expected post: `Post #1` (ID `p151110`), author `Post #1`
- Anchor text: "GPX-1b is a recently discovered transiting brown dwarf with a mass of 19.7 ± 1.6 MJup, and a radius of 1.47 ± 0.10 RJup, the first sub-stellar object discovered by the GPX ( G alactic P lane e X oplanet) survey!"
- Narrowing tokens: `oplanet`, `alactic`, `GPX-1b`, `MJup`

## TC-049
- Query: Find the forum post that mentions "tallClass "spacecraft"OrbitBarycenter "Sol/Orion_to_Mars"EllipticalOrbit{Period 1e32SemiMajorAxis 0}RotationPeriod 1e32RotationOffset 0}"Pulse_unit" "Sol" {Mesh "pulse_unitfix.cmod"Radius 0.02515 # 165 ft.".
- Expected thread file: `thread_10291.md`
- Expected post: `Post #22` (ID `p80503`), author `Post #29`
- Anchor text: "tallClass "spacecraft"OrbitBarycenter "Sol/Orion_to_Mars"EllipticalOrbit{Period 1e32SemiMajorAxis 0}RotationPeriod 1e32RotationOffset 0}"Pulse_unit" "Sol" {Mesh "pulse_unitfix.cmod"Radius 0.02515 # 165 ft."
- Narrowing tokens: `pulse_unitfix.cmod`, `e32RotationOffset`, `e32SemiMajorAxis`, `Orion_to_Mars`

## TC-050
- Query: Find the forum post that mentions "Bacon (AURA/STScI) View full size image "This planet has been studied well in the past, both by ourselves and other teams," said Fr?d?ric Pont of the University of Exeter, U.K., leader of the Hubble observing program in a statement.".
- Expected thread file: `thread_17339.md`
- Expected post: `Post #1` (ID `p133749`), author `Post #1`
- Anchor text: "Bacon (AURA/STScI) View full size image "This planet has been studied well in the past, both by ourselves and other teams," said Fr?d?ric Pont of the University of Exeter, U.K., leader of the Hubble observing program in a statement."
- Narrowing tokens: `Exeter`, `Bacon`, `U.K.`, `Pont`

## TC-051
- Query: Find the forum post that mentions "If you get really stuck, you can view the file ztree, hex mode, then change any byte value outside of 0x09, 0x0A, 0x0D, 0x20-0x7F to 0x20.".
- Expected thread file: `thread_17632.md`
- Expected post: `Post #13` (ID `p135883`), author `Post #9`
- Anchor text: "If you get really stuck, you can view the file ztree, hex mode, then change any byte value outside of 0x09, 0x0A, 0x0D, 0x20-0x7F to 0x20."
- Narrowing tokens: `x20-0x7F`, `x20.`, `x0D`, `x0A`

## TC-052
- Query: Find the forum post that mentions "In the 'pantry', you find a washing machine, a sink, a little 'workshop', a large freezer and the access to the cellar (cave, underground,...) Ah..a 'utility' or 'mechanical' room.".
- Expected thread file: `thread_17373.md`
- Expected post: `Post #1` (ID `p134081`), author `Post #4`
- Anchor text: "In the 'pantry', you find a washing machine, a sink, a little 'workshop', a large freezer and the access to the cellar (cave, underground,...) Ah..a 'utility' or 'mechanical' room."
- Narrowing tokens: `freezer`, `cellar`, `pantry`, `Ah..a`

## TC-053
- Query: Find the forum post that mentions "Color table from here Zip_2 Zip_3 Zip_4 p05.jpg An alternative map; with lakes of liquid METAL named Celestium, very rare in the galaxy.".
- Expected thread file: `thread_16987.md`
- Expected post: `Post #1` (ID `p130484`), author `Post #1`
- Anchor text: "Color table from here Zip_2 Zip_3 Zip_4 p05.jpg An alternative map; with lakes of liquid METAL named Celestium, very rare in the galaxy."
- Narrowing tokens: `Celestium`, `p05.jpg`, `Zip_3`, `Zip_4`

## TC-054
- Query: Find the forum post that mentions "Visual Studio no longer works...such a suprise and a shock I know how dependable microshaft is its a shock...".
- Expected thread file: `thread_17692.md`
- Expected post: `Post #1` (ID `p136255`), author `Post #1`
- Anchor text: "Visual Studio no longer works...such a suprise and a shock I know how dependable microshaft is its a shock..."
- Narrowing tokens: `works...such`, `dependable`, `microshaft`, `shock...`

## TC-055
- Query: Find the forum post that mentions "it was tucked against the east side of Greenland and the British Isles, and its mountain belts form part of a once-continuous chain that runs from Scandinavia to the Appalachians.".
- Expected thread file: `thread_5731.md`
- Expected post: `Post #2` (ID `p41966`), author `Post #9`
- Anchor text: "it was tucked against the east side of Greenland and the British Isles, and its mountain belts form part of a once-continuous chain that runs from Scandinavia to the Appalachians."
- Narrowing tokens: `once-continuous`, `Appalachians.`, `Scandinavia`, `tucked`

## TC-056
- Query: Find the forum post that mentions "In special relativity (->particle physics), the (non-gravitational) stress-energy tensor is a Noether current associated with spacetime translations and thus is componentwise conserved: d_nu T^{mu nu} = 0.".
- Expected thread file: `thread_15561.md`
- Expected post: `Post #24` (ID `p120411`), author `Post #46`
- Anchor text: "In special relativity (->particle physics), the (non-gravitational) stress-energy tensor is a Noether current associated with spacetime translations and thus is componentwise conserved: d_nu T^{mu nu} = 0."
- Narrowing tokens: `componentwise`, `stress-energy`, `Noether`, `d_nu`

## TC-057
- Query: Find the forum post that mentions "But fortunately I found here [http://messenger.jhuapl.edu/the_mission/mosaics.html](http://messenger.jhuapl.edu/the_mission/mosaics.html) color maps easyer to be worked (at least for mee), geotif and png format.".
- Expected thread file: `thread_17249.md`
- Expected post: `Post #1` (ID `p133661`), author `Post #10`
- Anchor text: "But fortunately I found here [http://messenger.jhuapl.edu/the_mission/mosaics.html](http://messenger.jhuapl.edu/the_mission/mosaics.html) color maps easyer to be worked (at least for mee), geotif and png format."
- Narrowing tokens: `mosaics.html`, `the_mission`, `easyer`, `geotif`

## TC-058
- Query: Find the forum post that mentions "Now I have COPYING_de, controls_de.txt, demo_de.cel and guide_de.cel ready for review; ~40 per cent of start_de.cel is also complete.".
- Expected thread file: `thread_11958.md`
- Expected post: `Post #11` (ID `p99546`), author `Post #11`
- Anchor text: "Now I have COPYING_de, controls_de.txt, demo_de.cel and guide_de.cel ready for review; ~40 per cent of start_de.cel is also complete."
- Narrowing tokens: `controls_de.txt`, `start_de.cel`, `guide_de.cel`, `demo_de.cel`

## TC-059
- Query: Find the forum post that mentions "[C:\Program Files\Celestia\extras\RCW79_3D\Double star.stc] "CCDM J13414-6152A:TYC 8991-538-1:HIP 66795:HD 118885:SAO 252413:PPM 360263:** JSP 591A:ALS 16970" #Double or multiple star CCDM J13414-6152AB.".
- Expected thread file: `thread_13791.md`
- Expected post: `Post #1` (ID `p115097`), author `Post #1`
- Anchor text: "[C:\Program Files\Celestia\extras\RCW79_3D\Double star.stc] "CCDM J13414-6152A:TYC 8991-538-1:HIP 66795:HD 118885:SAO 252413:PPM 360263:** JSP 591A:ALS 16970" #Double or multiple star CCDM J13414-6152AB."
- Narrowing tokens: `J13414-6152AB.`, `J13414-6152A`, `star.stc`, `RCW79_3D`

## TC-060
- Query: Find the forum post that mentions "Kind regards ### Code Snippets: ``` Modify "Titan" "Sol/Saturn"{info{Images ["info_Titan.jpg" , ""info_Titan2.jpg", ...]Discoverer "Christiaan Huygens"DiscoveryDate "1655"Mass 1.35e+23RelativeMass 2.2590e-02 #Earth = 1...RawText ["...".
- Expected thread file: `thread_9123.md`
- Expected post: `Post #23` (ID `p69957`), author `Post #27`
- Anchor text: "Kind regards ### Code Snippets: ``` Modify "Titan" "Sol/Saturn"{info{Images ["info_Titan.jpg" , ""info_Titan2.jpg", ...]Discoverer "Christiaan Huygens"DiscoveryDate "1655"Mass 1.35e+23RelativeMass 2.2590e-02 #Earth = 1...RawText ["..."
- Narrowing tokens: `info_Titan2.jpg`, `DiscoveryDate`, `RelativeMass`, `Discoverer`

## TC-061
- Query: Find the forum post that mentions "There is another planet past these 10, which represents an Espada that lost its rank due to another Espada's wrongdoings, I've put this one on a quasi-stable orbit crossing wide areas of the system, delicately stabilized by orbital resonances.".
- Expected thread file: `thread_19903.md`
- Expected post: `Post #1` (ID `p145962`), author `Post #1`
- Anchor text: "There is another planet past these 10, which represents an Espada that lost its rank due to another Espada's wrongdoings, I've put this one on a quasi-stable orbit crossing wide areas of the system, delicately stabilized by orbital resonances."
- Narrowing tokens: `quasi-stable`, `wrongdoings`, `resonances.`, `delicately`

## TC-062
- Query: Find the forum post that mentions "JoAnne Hewett [http://cosmicvariance.com/joanne/](http://cosmicvariance.com/joanne/) Fermilab/Chicago: Dr.".
- Expected thread file: `thread_11028.md`
- Expected post: `Post #8` (ID `p87226`), author `Post #22`
- Anchor text: "JoAnne Hewett [http://cosmicvariance.com/joanne/](http://cosmicvariance.com/joanne/) Fermilab/Chicago: Dr."
- Narrowing tokens: `cosmicvariance.com`, `JoAnne`, `Hewett`, `joanne`

## TC-063
- Query: Find the forum post that mentions "No, you cannot order them through us (except wholesale, in quantities, on our e-commerce site.) Otherwise, the closest thing you will find to a price is a UPC and/or an ISBN -- you'll have to find your own price through your favorite retailer or bookstore.".
- Expected thread file: `thread_14204.md`
- Expected post: `Post #3` (ID `p117287`), author `Post #3`
- Anchor text: "No, you cannot order them through us (except wholesale, in quantities, on our e-commerce site.) Otherwise, the closest thing you will find to a price is a UPC and/or an ISBN -- you'll have to find your own price through your favorite retailer or bookstore."
- Narrowing tokens: `e-commerce`, `bookstore.`, `retailer`, `ISBN`

## TC-064
- Query: Find the forum post that mentions "I’m bilingual, I have a D.E.C in Sc.Sociales from the C.E.G.E.P Lionel-groulx, I have 11 years of experience in education, more specifically at college level.".
- Expected thread file: `thread_5002.md`
- Expected post: `Post #1` (ID `p36373`), author `Post #1`
- Anchor text: "I’m bilingual, I have a D.E.C in Sc.Sociales from the C.E.G.E.P Lionel-groulx, I have 11 years of experience in education, more specifically at college level."
- Narrowing tokens: `Lionel-groulx`, `Sc.Sociales`, `C.E.G.E.P`, `bilingual`

## TC-065
- Query: Find the forum post that mentions "I install libraries liblua5.1-0-dev, liblua50-dev , liblualib50-dev and libjpeg-turbo8-dev I already have libpng12-0 and libpng12-dev I also already had a working QT5 development set of tools installed so my starting point might be a bit easier than some.".
- Expected thread file: `thread_17905.md`
- Expected post: `Post #7` (ID `p138053`), author `Post #5`
- Anchor text: "I install libraries liblua5.1-0-dev, liblua50-dev , liblualib50-dev and libjpeg-turbo8-dev I already have libpng12-0 and libpng12-dev I also already had a working QT5 development set of tools installed so my starting point might be a bit easier than some."
- Narrowing tokens: `libjpeg-turbo8-dev`, `liblualib50-dev`, `liblua50-dev`, `libpng12-dev`

## TC-066
- Query: Find the forum post that mentions "So thanks to your explanations I uderstood that in Celestia for an object orbitting round the Moon has the following hierarchy: UniversalCoord<-SolBarycenter<-EarthBarycenterAtACertainEpoch<-MoonAtACertainEpoch<-ObjectOrbittingMoonAtACertainEpoch.".
- Expected thread file: `thread_10311.md`
- Expected post: `Post #21` (ID `p80324`), author `Post #28`
- Anchor text: "So thanks to your explanations I uderstood that in Celestia for an object orbitting round the Moon has the following hierarchy: UniversalCoord<-SolBarycenter<-EarthBarycenterAtACertainEpoch<-MoonAtACertainEpoch<-ObjectOrbittingMoonAtACertainEpoch."
- Narrowing tokens: `ObjectOrbittingMoonAtACertainEpoch.`, `EarthBarycenterAtACertainEpoch`, `MoonAtACertainEpoch`, `SolBarycenter`

## TC-067
- Query: Find the forum post that mentions "At this stage, I'm leaning towards staying with a PC for the folowing reasons: An i-Mac is really just a big laptop, so comes with diminished graphics performance and less future expandability/flexibility.".
- Expected thread file: `thread_16845.md`
- Expected post: `Post #13` (ID `p129462`), author `Post #11`
- Anchor text: "At this stage, I'm leaning towards staying with a PC for the folowing reasons: An i-Mac is really just a big laptop, so comes with diminished graphics performance and less future expandability/flexibility."
- Narrowing tokens: `expandability`, `flexibility.`, `diminished`, `folowing`

## TC-068
- Query: Find the forum post that mentions "a/agua.htm And see the images below: Aposented spacebus: Astronauts: Einstein faces: Images of Pathfinder: Other funny images: Translation: Palmatop, the palm for poor people.".
- Expected thread file: `thread_5812.md`
- Expected post: `Post #1` (ID `p42586`), author `Post #1`
- Anchor text: "a/agua.htm And see the images below: Aposented spacebus: Astronauts: Einstein faces: Images of Pathfinder: Other funny images: Translation: Palmatop, the palm for poor people."
- Narrowing tokens: `Aposented`, `agua.htm`, `spacebus`, `Palmatop`

## TC-069
- Query: Find the forum post that mentions "This addon is created by me according to Slovak science-fiction of Vladimir Babula - Planeta troch slnc (The planet of three suns).".
- Expected thread file: `thread_20561.md`
- Expected post: `Post #1` (ID `p151659`), author `Post #1`
- Anchor text: "This addon is created by me according to Slovak science-fiction of Vladimir Babula - Planeta troch slnc (The planet of three suns)."
- Narrowing tokens: `Planeta`, `Babula`, `troch`, `slnc`

## TC-070
- Query: Find the forum post that mentions "The database on which the add-on is built is here: [http://tin.er.usgs.gov/mrds/find-mrds-intl.php](http://tin.er.usgs.gov/mrds/find-mrds-intl.php) That database has been robbed country by country and commodity by commodity.".
- Expected thread file: `thread_15617.md`
- Expected post: `Post #1` (ID `p120495`), author `Post #1`
- Anchor text: "The database on which the add-on is built is here: [http://tin.er.usgs.gov/mrds/find-mrds-intl.php](http://tin.er.usgs.gov/mrds/find-mrds-intl.php) That database has been robbed country by country and commodity by commodity."
- Narrowing tokens: `find-mrds-intl.php`, `tin.er.usgs.gov`, `commodity.`, `robbed`

## TC-071
- Query: Find the forum post that mentions "Value is clamped to the range [0.0,1.0].Type:float ``` ``` spec_r = (mat.spec*mat.specCol[0]) ``` ``` spec_r = (mat.specCol[0]) ``` ``` if mat.spec:spec_pwr = mat.spec......out.write('specpower %f\n' % (spec_pwr)) ```".
- Expected thread file: `thread_13488.md`
- Expected post: `Post #25` (ID `p117751`), author `Post #28`
- Anchor text: "Value is clamped to the range [0.0,1.0].Type:float ``` ``` spec_r = (mat.spec*mat.specCol[0]) ``` ``` spec_r = (mat.specCol[0]) ``` ``` if mat.spec:spec_pwr = mat.spec......out.write('specpower %f\n' % (spec_pwr)) ```"
- Narrowing tokens: `mat.spec......out.write`, `mat.specCol`, `spec_pwr`, `mat.spec`

## TC-072
- Query: Find the forum post that mentions "axe["ViDiBa asteroids:"] = "ViDiBa ast?ro?des:";["Asteroids00"] = "Ast?ro?des Ma Liste";["Asteroids01"] = "Ast?ro?des d.-g.".
- Expected thread file: `thread_17455.md`
- Expected post: `Post #9` (ID `p134727`), author `Post #10`
- Anchor text: "axe["ViDiBa asteroids:"] = "ViDiBa ast?ro?des:";["Asteroids00"] = "Ast?ro?des Ma Liste";["Asteroids01"] = "Ast?ro?des d.-g."
- Narrowing tokens: `Asteroids00`, `d.-g.`, `Liste`, `axe`

## TC-073
- Query: Find the forum post that mentions "Pour blender, j'ai désinstallé la version 2.7 et j'attends la prochaine (2.8) mais j'ai toujours le plugin en réserve...".
- Expected thread file: `thread_18024.md`
- Expected post: `Post #1154` (ID `p139764`), author `Post #579`
- Anchor text: "Pour blender, j'ai désinstallé la version 2.7 et j'attends la prochaine (2.8) mais j'ai toujours le plugin en réserve..."
- Narrowing tokens: `toujours`, `sinstall`, `serve...`, `attends`

## TC-074
- Query: Find the forum post that mentions "jets3.jpg jets2.jpg jets1.jpg New jets model made while eating my breakfast...".
- Expected thread file: `thread_17034.md`
- Expected post: `Post #150` (ID `p133003`), author `Post #67`
- Anchor text: "jets3.jpg jets2.jpg jets1.jpg New jets model made while eating my breakfast..."
- Narrowing tokens: `breakfast...`, `jets3.jpg`, `jets2.jpg`, `jets1.jpg`

## TC-075
- Query: Find the forum post that mentions "There's always news about the Cassini mission, Michelle Dougherty and Carl Murray make regular appearances, while the 2 Mars rovers recieve regular coverage too - Steve Squyres was interviewed earlier in the year.".
- Expected thread file: `thread_15962.md`
- Expected post: `Post #1` (ID `p122886`), author `Post #1`
- Anchor text: "There's always news about the Cassini mission, Michelle Dougherty and Carl Murray make regular appearances, while the 2 Mars rovers recieve regular coverage too - Steve Squyres was interviewed earlier in the year."
- Narrowing tokens: `interviewed`, `Dougherty`, `Michelle`, `Squyres`

## TC-076
- Query: Find the forum post that mentions "warning: preg_replace_callback(): Requires argument 2, '_decode_entities("$1", "$2", "$0", $newtable, $exclude)', to be a valid callback in /public/vhost/c/cm/html/includes/unicode.inc on line 345.".
- Expected thread file: `thread_19884.md`
- Expected post: `Post #1` (ID `p145852`), author `Post #1`
- Anchor text: "warning: preg_replace_callback(): Requires argument 2, '_decode_entities("$1", "$2", "$0", $newtable, $exclude)', to be a valid callback in /public/vhost/c/cm/html/includes/unicode.inc on line 345."
- Narrowing tokens: `preg_replace_callback`, `decode_entities`, `unicode.inc`, `newtable`

## TC-077
- Query: Find the forum post that mentions "In lua 5.3, the following functions are deprecated in the mathematical library: atan2, cosh, sinh, tanh, pow, frexp, and ldexp.".
- Expected thread file: `thread_17371.md`
- Expected post: `Post #19` (ID `p140492`), author `Post #13`
- Anchor text: "In lua 5.3, the following functions are deprecated in the mathematical library: atan2, cosh, sinh, tanh, pow, frexp, and ldexp."
- Narrowing tokens: `ldexp.`, `frexp`, `sinh`, `cosh`

## TC-078
- Query: Find the forum post that mentions ""Agirhenes" should be Agasthenes, "Agirrophus" should be Agastrophus, "Aliror" should be Alastor, "Atreropaios" should be Asteropaios, and "Atryanax" should be Astyanax.".
- Expected thread file: `thread_18410.md`
- Expected post: `Post #31` (ID `no-id-viewtopic.php__fc73edbb.html-5134`), author `unknown`
- Anchor text: ""Agirhenes" should be Agasthenes, "Agirrophus" should be Agastrophus, "Aliror" should be Alastor, "Atreropaios" should be Asteropaios, and "Atryanax" should be Astyanax."
- Narrowing tokens: `Agastrophus`, `Asteropaios`, `Atreropaios`, `Agasthenes`

## TC-079
- Query: Find the forum post that mentions "[http://www.unternehmen.com/Bernhard-Michel/MieCalc/eindex.html](http://www.unternehmen.com/Bernhard-Michel/MieCalc/eindex.html) (english version) there are many other sites...".
- Expected thread file: `thread_16156.md`
- Expected post: `Post #5` (ID `p124578`), author `Post #9`
- Anchor text: "[http://www.unternehmen.com/Bernhard-Michel/MieCalc/eindex.html](http://www.unternehmen.com/Bernhard-Michel/MieCalc/eindex.html) (english version) there are many other sites..."
- Narrowing tokens: `www.unternehmen.com`, `Bernhard-Michel`, `eindex.html`, `sites...`

## TC-080
- Query: Find the forum post that mentions "is: %s", SelectionKeyValue )celestia:print(ValueString)elsecelestia:print(" Please select a Planet or Moon:")endend-- ----------------------- START PROGRAMExit = falserepeatwait(0)FindKeyValue( )until Exit ```".
- Expected thread file: `thread_15968.md`
- Expected post: `Post #1` (ID `p122953`), author `Post #1`
- Anchor text: "is: %s", SelectionKeyValue )celestia:print(ValueString)elsecelestia:print(" Please select a Planet or Moon:")endend-- ----------------------- START PROGRAMExit = falserepeatwait(0)FindKeyValue( )until Exit ```"
- Narrowing tokens: `SelectionKeyValue`, `falserepeatwait`, `FindKeyValue`, `ValueString`

## TC-081
- Query: Find the forum post that mentions "I just suffered a C atastrophic R azing A nd S ystemic Halt, courtesy of our benevolent dictator, Mr.".
- Expected thread file: `thread_8160.md`
- Expected post: `Post #6` (ID `p62350`), author `Post #6`
- Anchor text: "I just suffered a C atastrophic R azing A nd S ystemic Halt, courtesy of our benevolent dictator, Mr."
- Narrowing tokens: `atastrophic`, `benevolent`, `ystemic`, `azing`

## TC-082
- Query: Find the forum post that mentions "For example, instead of just using one 'extras " folder, you can create 3 or 5 or 20 folders named " extras-new", extras-experimental", extras-deep space", extras1, extras2, etc .".
- Expected thread file: `thread_11988.md`
- Expected post: `Post #1` (ID `p99698`), author `Post #1`
- Anchor text: "For example, instead of just using one 'extras " folder, you can create 3 or 5 or 20 folders named " extras-new", extras-experimental", extras-deep space", extras1, extras2, etc ."
- Narrowing tokens: `extras-experimental`, `extras-deep`, `extras-new`, `extras2`

## TC-083
- Query: Find the forum post that mentions "plugins_locale.zip create the translation file(s) This is the tranlation file for French Code: Select all -- Separation angles -- French translation file sepAngles_loc_str = { ["Angular separation"] = "S?paration angulaire"; ["Sep.".
- Expected thread file: `thread_17141.md`
- Expected post: `Post #16` (ID `p132521`), author `Post #17`
- Anchor text: "plugins_locale.zip create the translation file(s) This is the tranlation file for French Code: Select all -- Separation angles -- French translation file sepAngles_loc_str = { ["Angular separation"] = "S?paration angulaire"; ["Sep."
- Narrowing tokens: `plugins_locale.zip`, `sepAngles_loc_str`, `tranlation`, `angulaire`

## TC-084
- Query: Find the forum post that mentions "The error message read "connect to cvs.sourceforge.net:2401 failed: Der Host war bei einem Socketvorgang nicht erreichbar." (in German).".
- Expected thread file: `thread_6255.md`
- Expected post: `Post #24` (ID `p75083`), author `Post #36`
- Anchor text: "The error message read "connect to cvs.sourceforge.net:2401 failed: Der Host war bei einem Socketvorgang nicht erreichbar." (in German)."
- Narrowing tokens: `Socketvorgang`, `erreichbar.`, `einem`, `bei`

## TC-085
- Query: Find the forum post that mentions "After mounting it using MagicISO, I had no problems playing it and viewing various sections with both PowerDVD v10 and Kodi v18 alpha under Win7.".
- Expected thread file: `thread_17749.md`
- Expected post: `Post #3` (ID `p136519`), author `Post #7`
- Anchor text: "After mounting it using MagicISO, I had no problems playing it and viewing various sections with both PowerDVD v10 and Kodi v18 alpha under Win7."
- Narrowing tokens: `MagicISO`, `PowerDVD`, `v10`, `v18`

## TC-086
- Query: Find the forum post that mentions "A similar kind of techniques were applied also in the audio-restoration realm years ago; either to add harmonics to the bass line or in modelling the noise floor of the tape to S/N ratio, before to develop specific softwares.".
- Expected thread file: `thread_17181.md`
- Expected post: `Post #3` (ID `p132374`), author `Post #6`
- Anchor text: "A similar kind of techniques were applied also in the audio-restoration realm years ago; either to add harmonics to the bass line or in modelling the noise floor of the tape to S/N ratio, before to develop specific softwares."
- Narrowing tokens: `audio-restoration`, `softwares.`, `harmonics`, `bass`

## TC-087
- Query: Find the forum post that mentions "I think that the 3D graphics community needs its own version of physicist John Baez's Crackpot Index: [http://math.ucr.edu/home/baez/crackpot.html](http://math.ucr.edu/home/baez/crackpot.html) --Chris".
- Expected thread file: `thread_15823.md`
- Expected post: `Post #5` (ID `p121944`), author `Post #3`
- Anchor text: "I think that the 3D graphics community needs its own version of physicist John Baez's Crackpot Index: [http://math.ucr.edu/home/baez/crackpot.html](http://math.ucr.edu/home/baez/crackpot.html) --Chris"
- Narrowing tokens: `crackpot.html`, `math.ucr.edu`, `Crackpot`, `Baez`

## TC-088
- Query: Find the forum post that mentions "TERRIER wrote: Maybe the England players should be asked to walk past those magnets carrying a container of their choice made from either steel, carbon fibre, or wood (maybe with a sneaky nail hammered in).".
- Expected thread file: `thread_15978.md`
- Expected post: `Post #1` (ID `p123206`), author `Post #42`
- Anchor text: "TERRIER wrote: Maybe the England players should be asked to walk past those magnets carrying a container of their choice made from either steel, carbon fibre, or wood (maybe with a sneaky nail hammered in)."
- Narrowing tokens: `hammered`, `sneaky`, `fibre`, `magnets`

## TC-089
- Query: Find the forum post that mentions "cel://Freeflight/2006-06-04T12:58:23.58341?x=AIAAdHGt+CnqmFY&y=AGDa7CQQ1WaV2AEB&z=AGCCR5u9TxzsuaL9/////w&ow=0.784756&ox=0.243625&oy=0.503294&oz=0.267397&select=HIP15776&fov=31.813145&ts=1000000.000000&ltd=0&rf=40855&lm=49154".
- Expected thread file: `thread_5065.md`
- Expected post: `Post #69` (ID `p71262`), author `Post #64`
- Anchor text: "cel://Freeflight/2006-06-04T12:58:23.58341?x=AIAAdHGt+CnqmFY&y=AGDa7CQQ1WaV2AEB&z=AGCCR5u9TxzsuaL9/////w&ow=0.784756&ox=0.243625&oy=0.503294&oz=0.267397&select=HIP15776&fov=31.813145&ts=1000000.000000&ltd=0&rf=40855&lm=49154"
- Narrowing tokens: `AGDa7CQQ1WaV2AEB`, `AGCCR5u9TxzsuaL9`, `AIAAdHGt`, `HIP15776`

## TC-090
- Query: Find the forum post that mentions "They were all from published literature (Yale, McCormick, Cape of Good Hope, Allegheny, USNO) or spectro/photometric distances from published literature (eg, Weis).".
- Expected thread file: `thread_16318.md`
- Expected post: `Post #1` (ID `p125722`), author `Post #3`
- Anchor text: "They were all from published literature (Yale, McCormick, Cape of Good Hope, Allegheny, USNO) or spectro/photometric distances from published literature (eg, Weis)."
- Narrowing tokens: `Allegheny`, `McCormick`, `spectro`, `Weis`

## TC-091
- Query: Find the forum post that mentions "It doesn?t make sense.Both Hyperion and Itokawa are irregular bodies.Both have cmod models.However,I can see texture on Hyperion,but not in Itokawa.The Itokawa mosaic texture was from Phil Stooke.What?s going on?".
- Expected thread file: `thread_16166.md`
- Expected post: `Post #1` (ID `p124591`), author `Post #1`
- Anchor text: "It doesn?t make sense.Both Hyperion and Itokawa are irregular bodies.Both have cmod models.However,I can see texture on Hyperion,but not in Itokawa.The Itokawa mosaic texture was from Phil Stooke.What?s going on?"
- Narrowing tokens: `models.However`, `bodies.Both`, `Itokawa.The`, `Stooke.What`

## TC-092
- Query: Find the forum post that mentions "So, here you are: New Lemmon 5 sec std.jpg Panstarrs sobre Bariloche 2 (2806).jpg Panstarrs sobre Cerro Catedral (2811).jpg".
- Expected thread file: `thread_17305.md`
- Expected post: `Post #1` (ID `p133485`), author `Post #1`
- Anchor text: "So, here you are: New Lemmon 5 sec std.jpg Panstarrs sobre Bariloche 2 (2806).jpg Panstarrs sobre Cerro Catedral (2811).jpg"
- Narrowing tokens: `Catedral`, `std.jpg`, `sobre`, `Cerro`

## TC-093
- Query: Find the forum post that mentions "And the effects would likely be much worse than the 1859 Carrington Event, a solar superstorm that wreaked havoc on telegraph lines and caused the aurora borealis to be visible as far south as Texas.".
- Expected thread file: `thread_17196.md`
- Expected post: `Post #1` (ID `p132470`), author `Post #1`
- Anchor text: "And the effects would likely be much worse than the 1859 Carrington Event, a solar superstorm that wreaked havoc on telegraph lines and caused the aurora borealis to be visible as far south as Texas."
- Narrowing tokens: `superstorm`, `Carrington`, `telegraph`, `wreaked`

## TC-094
- Query: Find the forum post that mentions "dans Celestia, essayez ctrl "v", plusieurs fois pour changer le comportement de OpenGl In Celestia, try ctrl "v" several times to change the behavior of OpenGl".
- Expected thread file: `thread_17487.md`
- Expected post: `Post #9` (ID `p135597`), author `Post #13`
- Anchor text: "dans Celestia, essayez ctrl "v", plusieurs fois pour changer le comportement de OpenGl In Celestia, try ctrl "v" several times to change the behavior of OpenGl"
- Narrowing tokens: `comportement`, `plusieurs`, `essayez`, `fois`

## TC-095
- Query: Find the forum post that mentions "Fridger ### Code Snippets: ``` lowpass from=moon_5uvvis_500m.raw.cub to=output.cub samples=130 lines=11 filter=outside null=yes hrs=no his=no lrs=no lis=no replacement=center ```".
- Expected thread file: `thread_13856.md`
- Expected post: `Post #3` (ID `p115636`), author `Post #14`
- Anchor text: "Fridger ### Code Snippets: ``` lowpass from=moon_5uvvis_500m.raw.cub to=output.cub samples=130 lines=11 filter=outside null=yes hrs=no his=no lrs=no lis=no replacement=center ```"
- Narrowing tokens: `moon_5uvvis_500m.raw.cub`, `output.cub`, `lowpass`, `lrs`

## TC-096
- Query: Find the forum post that mentions "[https://spacecruft.org/spacecruft/celestia-galmon](https://spacecruft.org/spacecruft/celestia-galmon) Galmon FYI: [https://galmon.eu](https://galmon.eu) [https://galmon.eu/observers.html](https://galmon.eu/observers.html) -Jeff".
- Expected thread file: `thread_22559.md`
- Expected post: `Post #10` (ID `p157773`), author `Post #4`
- Anchor text: "[https://spacecruft.org/spacecruft/celestia-galmon](https://spacecruft.org/spacecruft/celestia-galmon) Galmon FYI: [https://galmon.eu](https://galmon.eu) [https://galmon.eu/observers.html](https://galmon.eu/observers.html) -Jeff"
- Narrowing tokens: `celestia-galmon`, `observers.html`, `galmon.eu`, `Galmon`

## TC-097
- Query: Find the forum post that mentions "Guillermo (NASA's video and applet: [http://svs.gsfc.nasa.gov/vis/a000000/a003800/a003894/](http://svs.gsfc.nasa.gov/vis/a000000/a003800/a003894/) )".
- Expected thread file: `thread_14062.md`
- Expected post: `Post #30` (ID `p129211`), author `Post #82`
- Anchor text: "Guillermo (NASA's video and applet: [http://svs.gsfc.nasa.gov/vis/a000000/a003800/a003894/](http://svs.gsfc.nasa.gov/vis/a000000/a003800/a003894/) )"
- Narrowing tokens: `svs.gsfc.nasa.gov`, `a000000`, `a003800`, `a003894`

## TC-098
- Query: Find the forum post that mentions "Graphics version: graphics-version.jpg My settings: graphics-settings.jpg Default settings: graphics-defaults.jpg A while ago I tried to upgrade the drivers for this chipset but it crashed or bluescreened the computer, so had to rollback.".
- Expected thread file: `thread_13397.md`
- Expected post: `Post #1` (ID `p111667`), author `Post #1`
- Anchor text: "Graphics version: graphics-version.jpg My settings: graphics-settings.jpg Default settings: graphics-defaults.jpg A while ago I tried to upgrade the drivers for this chipset but it crashed or bluescreened the computer, so had to rollback."
- Narrowing tokens: `graphics-settings.jpg`, `graphics-defaults.jpg`, `graphics-version.jpg`, `bluescreened`

## TC-099
- Query: Find the forum post that mentions "200.bin.gz However the "Global Multi-resolution Terrain Elevation Data 2010 (GMTED2010)" is in ArcGIS database format -- yes GDAL can convert it to a GTiff but the ds15 is NOT a full map.".
- Expected thread file: `thread_17392.md`
- Expected post: `Post #1` (ID `p134187`), author `Post #1`
- Anchor text: "200.bin.gz However the "Global Multi-resolution Terrain Elevation Data 2010 (GMTED2010)" is in ArcGIS database format -- yes GDAL can convert it to a GTiff but the ds15 is NOT a full map."
- Narrowing tokens: `GMTED2010`, `bin.gz`, `GTiff`, `ds15`

## TC-100
- Query: Find the forum post that mentions "If one switches on -msse -msse2 -mmmx options then the non-CUDA suported code also becomes pretty usable.".
- Expected thread file: `thread_10856.md`
- Expected post: `Post #1` (ID `p85192`), author `Post #1`
- Anchor text: "If one switches on -msse -msse2 -mmmx options then the non-CUDA suported code also becomes pretty usable."
- Narrowing tokens: `suported`, `non-CUDA`, `mmmx`, `msse`
