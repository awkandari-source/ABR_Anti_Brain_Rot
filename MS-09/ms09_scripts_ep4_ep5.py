#!/usr/bin/env python3
"""
MS-09 ("Earth's Slowest Clocks — Volume II") — Episodes 4 and 5 Locked Scripts (ABR-AG-SOP-v2.1)
================================================================================================
Strict ABR-AG-SOP-v2.1 Spec:
- Continuous Master Voice Track (Stem 1) with 0 per-scene audio padding (`apad` forbidden)
- Decoupled visual holds (>= 15.0s net hold + 1.0s cross-dissolve overlaps across exact 901.00s / 15:01)
- Spoken Word Budget: strictly 1,650 - 1,850 words per 15-minute episode (110 - 120 WPM, >= 88% vocal duty)
- Zero ellipses (`...`), zero `[PAUSE >= 1.5s]` markers, zero background music.
"""

from __future__ import annotations

MS09_E04_LINES: list[tuple[int, str]] = [
    # Segment A (01..07): Opening Immersion Along the Mid-Ocean Ridge Rift Valley
    (1, "Three thousand meters beneath the calm twilight swells of the Atlantic, Pacific, and Indian oceans, an unbroken underwater mountain chain winds sixty-five thousand kilometers around Earth like the seam of a baseball. It is the longest geological feature on our planet."),
    (1, "Down inside the quiet axial rift valley along the crest of this mid-ocean ridge, no surface gale ever stirs the near-freezing abyssal water, and deep currents glide in velvet silence. Perpetual darkness cradles the valley floor."),
    (2, "Along narrow volcanic fissures on the valley floor, warm basaltic magma rises gently from Earth's upper mantle and meets cold seawater, rounding smoothly into dark stone lobes called pillow basalt. Each rounded pillow cools quietly into solid crust."),
    (6, "Nearby, slender sulfide mineral chimneys release slow, shimmering plumes of warm mineral water into the dark sea, while freshly quenched volcanic glass cools peacefully with subtle, faint mineral crackles."),
    (3, "To an unaided eye peering through a submersible viewport, one dark ridge of seafloor basalt looks identical to the older volcanic slopes resting fifty or five hundred kilometers away beneath clay."),
    (4, "Yet locked inside microscopic iron-oxide grains throughout that oceanic crust lies a symmetrical magnetic tape recording spanning one hundred eighty million years of drifting continents and reversing poles. Solid rock remembers the sky's invisible compass."),
    (7, "Welcome to Episode Four of Earth's Slowest Clocks, Volume Two: magnetic stripes and the ocean floor tape recorder chronicled in the United States Geological Survey classic This Dynamic Earth."),

    # Segment B (08..26): Magnetite Curie-Point Locking, Towed Magnetometers & Vine-Matthews-Morley
    (4, "To understand how solid seafloor stone records invisible planetary magnetism, zoom gently inward to the microscopic crystal lattice of freshly erupted mid-ocean ridge basalt. Inside dark volcanic glass sit millions of tiny mineral grains."),
    (4, "Crystallizing early within cooling basaltic lava are tiny octahedral grains of magnetite and titanomagnetite, iron-oxide minerals naturally responsive to ambient magnetic fields."),
    (2, "When pillow lava first emerges onto the deep rift floor near twelve hundred degrees Celsius, vigorous thermal vibration keeps atomic magnetic moments inside those grains pointing in random directions. Intense warmth prevents any fixed magnetic alignment."),
    (4, "As cold abyssal seawater patiently draws heat out of the stone, however, the solidifying basalt crosses a pivotal physical threshold near five hundred eighty degrees Celsius known as the Curie point."),
    (4, "Below the Curie temperature, thermal agitation quiets enough for magnetic domains inside every tiny magnetite crystal to align faithfully with Earth's surrounding geomagnetic field like miniature compass needles. Every crystal settles into calm unison."),
    (2, "Once the volcanic rock cools completely down to two-degree seabed equilibrium, that thermoremanent magnetic orientation remains locked in solid oceanic crust for hundreds of millions of years."),
    (8, "Meanwhile, slow convection inside Earth's mantle draws the two neighboring tectonic plates apart at the unhurried pace at which a human fingernail grows—barely two to five centimeters per calm year. Continents drift without jarring or haste."),
    (1, "Century after century, fresh basalt wells upward along the central seam to heal the parting crust, carrying older magnetized rock steadily outward in both directions like twin conveyor belts."),
    (5, "Well into the middle of the twentieth century, most geologists pictured the deep ocean floor as an ancient, static basin that had simply collected sediment since Earth's seas first formed. Few imagined the seabed was continually renewed."),
    (5, "Then, across the calm post-war years of the nineteen fifties, oceanographic research vessels began towing slender brass fluxgate and proton-precession magnetometers back and forth across open oceans."),
    (5, "During systematic marine surveys off the Pacific Northwest along the Juan de Fuca Ridge and across the Reykjanes Ridge south of Iceland, Ronald Mason, Arthur Raff, and colleagues mapped a startling pattern. Their paper charts revealed unmistakable order."),
    (3, "Instead of smooth, uniform magnetic readings, the ocean floor revealed remarkably regular, parallel zebra stripes of slightly stronger and slightly weaker magnetic intensity stretching hundreds of kilometers."),
    (3, "Even more remarkably, the sequence of wide and narrow magnetic bands on the western flank of each mid-ocean ridge formed a faithful mirror image of the eastern flank. Both sides matched band for band."),
    (7, "Why would the hidden volcanic bedrock beneath every ocean on Earth organize itself into twin symmetrical barcodes centered directly upon deep submarine ridge crests?"),
    (7, "In September nineteen sixty-three, Cambridge geophysicists Frederick Vine and Drummond Matthews—and independently Canadian earth scientist Lawrence Morley—united two bold insights into one serene, unifying hypothesis. Plate tectonics suddenly gained its clearest proof."),
    (6, "First, Harry Hess and Robert Dietz had proposed seafloor spreading: that young oceanic crust forms continuously along mid-ocean ridges and glides laterally outward across geological time."),
    (7, "Second, paleomagnetists including Bernard Brunhes, Motonori Matuyama, Allan Cox, Richard Doell, and Brent Dalrymple had shown from radiometrically dated land lavas that Earth's magnetic field periodically flips polarity."),
    (3, "During normal polarity chrons like our modern Brunhes epoch, magnetic compasses point toward geographic north; during reversed chrons, fluid iron currents in Earth's outer core flip smoothly southward. Neither state disturbs life on the surface above."),
    (3, "Wherever steady seafloor spreading meets periodic geomagnetic reversals, each normal epoch freezes a positively magnetized stripe of basalt, and each reversed epoch freezes a negatively magnetized twin."),

    # Segment C (27..45): The 180-Million-Year Geomagnetic Polarity Time Scale & Deep-Sea Drilling
    (5, "When a research vessel glides calmly above normal-polarity seafloor basalt, the ancient stone's locked magnetism adds subtly to Earth's modern dipole field, tracing a gentle positive anomaly. Sensitive instruments read that ancient whisper through kilometers of water."),
    (5, "Half an hour later, as the ship crosses smoothly over an adjacent basalt band cooled during a reversed epoch, the fossilized magnetism subtracts slightly from today's ambient field."),
    (7, "Unmistakable physical proof arrived in nineteen sixty-eight when the deep-sea drilling ship Glomar Challenger recovered cylindrical basalt and chalk cores along an east-west transect across the South Atlantic. Each core brought deep time up into warm daylight."),
    (7, "Laid out inside wooden core trays under warm shipboard lamp light, microfossils resting directly atop the basalt crust grew systematically older in linear proportion to distance from the ridge."),
    (3, "Correlating potassium-argon dated lava reversals on land with global marine magnetometer profiles established the Geomagnetic Polarity Time Scale across every ocean basin on Earth. Every stripe received an exact geological age."),
    (3, "Notice how calm yet unhurriedly irregular Earth's outer-core geodynamo truly is: the most recent full reversal, the Brunhes-Matuyama transition, unfolded roughly seven hundred eighty thousand years ago."),
    (4, "Across the past sixty-six million years of the Cenozoic Era, reversals occurred every few hundred thousand years on average, each flip taking several thousand peaceful years to complete. Slow core eddies guide every transition."),
    (8, "Sail farther outward toward the quiet continental margins into mid-Cretaceous seafloor, however, and magnetometers cross a broad, tranquil expanse completely free of reversals for nearly forty million years."),
    (8, "Geophysicists call that serene interval between one hundred twenty-one and eighty-three million years ago the Cretaceous Normal Superchron, when Earth's magnetic shield held one steady orientation."),
    (3, "Beyond that quiet superchron, inside the oldest surviving abyssal basins of the western Pacific and northwest Atlantic, Jurassic magnetic stripes extend the seafloor record back one hundred eighty million years. Early dinosaurs walked on land when that basalt cooled."),
    (8, "Why does the ocean floor magnetic tape recorder conclude near one hundred eighty million years when ancient continental shield rocks preserve more than three billion years of history?"),
    (8, "Because aging oceanic lithosphere cools, thickens, and grows dense enough to descend peacefully back into the mantle along deep ocean trenches, recycling seafloor stone in a grand planetary cycle."),
    (3, "Even so, one hundred eighty million unbroken years of symmetrical magnetic isochrons allow geologists to rewind the opening of the Atlantic, Indian, and Southern oceans kilometer by kilometer. Every ancient coastline fits cleanly back together."),
    (5, "Matching identical magnetic stripes from the South American margin back against the African margin reveals ancient Pangaea parting at the calm, steady speed of a growing fingernail."),
    (6, "Along slow-spreading ridges such as the Mid-Atlantic Ridge and the ultra-slow Arctic Gakkel Ridge, a single kilometer of basalt width archives fifty thousand to one hundred thousand quiet years."),
    (2, "Along faster-spreading Pacific ridges like the East Pacific Rise, wider volcanic bands capture brief geomagnetic excursions and delicate intensity shifts with extraordinary horizontal clarity. Fast and slow ridges tell the exact same story."),
    (6, "All along those submarine mountain chains tonight, warm hydrothermal vents circulate deep seawater quietly through cracked basalt, balancing ocean chemistry across ages."),
    (4, "No human scribe, brass instrument, or parchment map was ever needed to chronicle continental drift; microscopic iron-oxide grains cooling in dark abyssal water remembered every centimeter."),
    (7, "From tiny mineral compasses locked peacefully below five hundred eighty degrees Celsius, humanity discovered that Earth's crust glides in patient, unbroken geological order. Still stone holds dynamic memory."),

    # Segment D (46..56): Evening Wind-Down & Bridge to Shark Bay's Living Stromatolites
    (8, "Tonight, let your waking attention drift slowly downward through three kilometers of calm dark ocean onto that vast abyssal plain, blanketed in soft golden-brown marine clay."),
    (2, "Beneath that quiet sediment blanket, ancient pillow basalts rest in cool two-degree stillness, faithfully holding the exact magnetic alignment of distant Jurassic and Cretaceous afternoons. Nothing down there ever hurries."),
    (1, "Along the faraway axial rift valley, Earth adds tomorrow's seafloor without noise or haste, widening whole ocean basins by half a thumb's breadth across an entire calm year."),
    (6, "Low abyssal currents move effortlessly past warm mineral chimneys, carrying gentle geothermal warmth outward into boundless, undisturbed deep water. Darkness feels warm and sheltering."),
    (7, "Nearly three thousand kilometers deeper still inside Earth's liquid iron outer core, slow convective currents sustain the invisible magnetic shield cradling our sleeping planet tonight."),
    (4, "Like microscopic magnetite grains coming gently into calm alignment as warm rock cools below its Curie point, scattered daytime thoughts settle naturally as evening cools. Rest brings effortless inner order."),
    (8, "Nothing across the deep ocean floor ever rushes to reach a distant shore; two centimeters a year is swift enough to part continents and shape calm seas."),
    (1, "Let the low, steady hum of deep abyssal water movement and subtle cooling stone release every trace of tension from your chest and shoulders."),
    (8, "You rest securely tonight upon a slow, trustworthy planet whose deepest foundations move in quiet, predictable harmony. Every deep current carries you toward sleep."),
    (5, "In Episode Five, our finale of Earth's Slowest Clocks, Volume Two, we ascend from the dark basalt abyss into the warm turquoise shallows of Shark Bay in Western Australia."),
    (8, "Waiting in sunlit tidal water stand Earth's oldest living stone builders—layered microbial stromatolites spanning three point five billion years. Sleep deeply tonight."),
]


MS09_E05_LINES: list[tuple[int, str]] = [
    # Segment A (01..07): Opening Immersion at Hamelin Pool, Shark Bay
    (1, "Along the sun-warmed Indian Ocean coast of Western Australia, soft amber evening light pours across the shallow, mirror-calm waters of Hamelin Pool at the southern reach of Shark Bay. Golden dusk stretches peacefully from horizon to shore."),
    (6, "A gentle warm breeze whispers across white coquina shell beaches and delicate salt-crusted flats, raising barely a faint ripple along the clear turquoise-and-bronze lagoon margin. Everything along this remote bay breathes in slow motion."),
    (2, "Wading ankle-deep in quiet imagination along this sheltered shore, you notice hundreds of rounded, cushion-shaped domes rising calmly through the gentle tidal wash like weathered coastal boulders."),
    (2, "Observe those submerged mounds with a patient naturalist's eye, however, and you discover they are not lifeless wave-worn stones eroded down from older desert cliffs. Each rounded dome is quietly alive."),
    (4, "Blanketing the sunlit upper millimeter of every dome thrives a soft, velvety microbial mat of billions of photosynthetic cyanobacteria, patiently building solid limestone upward grain by grain."),
    (3, "Slice vertically into an ancient fossilized relative from inland Pilbara bedrock, and fine wavy carbonate laminae carry this exact living architecture backward three point five billion years. Nearly four-fifths of Earth's history rests inside this form."),
    (7, "Welcome to Episode Five, the series finale of Earth's Slowest Clocks, Volume Two: stromatolites, the three-point-five-billion-year living stones chronicled in the United States Geological Survey Stromatolites Archive."),

    # Segment B (08..26): Cyanobacteria Mats, Hypersaline Sanctuary & Millimeter Accretion
    (4, "How do microscopic single-celled organisms completely invisible to the unaided eye construct durable stone monuments sturdy enough to outlast entire continental mountain ranges? Their secret lies in unhurried daily cooperation."),
    (4, "The word stromatolite derives from classical Greek roots meaning layered rock, introduced by geologists to describe laminated carbonate structures accreted through the quiet daily work of benthic microbial mats."),
    (4, "Across the sunlit crest of each living dome inside Hamelin Pool stretch interwoven filaments of cyanobacteria, wrapped inside a translucent, protective sheath of natural extracellular mucilage. That soft gel shields the cells from bright sun."),
    (2, "Whenever a gentle incoming tide washes fine suspended grains of calcium carbonate sand and aragonite silt over the dome, sticky microbial filaments trap and hold tiny mineral particles."),
    (4, "Simultaneously, as sunlit cyanobacteria carry out oxygenic photosynthesis during calm daytime hours, they draw dissolved carbon dioxide out of surrounding pore water, gently raising local pH and alkalinity. Sunlight quietly guides mineral chemistry."),
    (4, "That quiet micro-chemical shift coaxes dissolved calcium and bicarbonate ions in the warm lagoon water to precipitate microscopic needles of aragonite cement directly around the trapped grains."),
    (3, "Whenever a thin new mineral veil begins shading the light-seeking microbes from tomorrow's sun, motile cyanobacteria filaments glide slowly upward by fractions of a millimeter to weave a fresh surface mat. Life steps gently atop yesterday's stone."),
    (3, "Left peacefully behind them is one wafer-thin lamina solidified into permanent limestone—a single microscopic step in a biological craft older than every tree, coral, and animal on Earth."),
    (2, "At what unhurried tempo does a living marine stromatolite rise inside the tranquil shallow waters of Hamelin Pool at Shark Bay? Even coastal lichens grow swiftly by comparison."),
    (2, "Long-term field measurements show each rounded head accretes upward at roughly zero point three to zero point four millimeters per year—barely one single millimeter every three calm years."),
    (1, "A living stromatolite dome standing just half a meter tall in tonight's warm evening tide has spent well over fifteen hundred patient years rising millimeter by millimeter through clear water. Centuries pass within the width of a palm."),
    (1, "Why do living marine stromatolites flourish in thousands across Hamelin Pool while remaining exceedingly rare along almost every other modern ocean shoreline on our planet?"),
    (6, "Across the northern entrance of Hamelin Pool stretches a broad, shallow sand and seagrass barrier called the Faure Sill, quietly restricting tidal water exchange with the open Indian Ocean. Shallow geometry creates a natural refuge."),
    (6, "Under Western Australia's warm, dry subtropic sun, steady evaporation concentrates the sheltered lagoon water until its salinity reaches roughly twice that of ordinary coastal seawater."),
    (2, "Inside that serene hypersaline sanctuary, grazing marine snails, sea urchins, and burrowing worms that ordinarily consume soft microbial mats along open coasts cannot comfortably graze. Gentle saltiness protects the ancient builders."),
    (1, "Sheltered from hungry grazers and sediment-churning burrowers, Shark Bay's cyanobacteria communities build undisturbed stone domes just as their ancestors did across young Earth's seas."),
    (5, "Walking quietly along the timber viewing walkway above Hamelin Pool at dusk therefore feels like looking directly through a calm window into the Archean and Proterozoic eons. Deep planetary memory rests in plain view."),
    (7, "Billions of years before trilobites crossed Cambrian sand or green mosses touched damp coastal rock, sunlit shallow lagoons around every young continent looked remarkably like this bay."),
    (3, "Every undulating millimeter preserved inside polished stromatolite stone records an unbroken daily conversation between warm sunlight, gentle shallow tides, and patient microscopic life."),

    # Segment C (27..45): Pilbara 3.5-Billion-Year Fossils, Oxygenation & Deep-Time Synthesis
    (7, "Barely six hundred kilometers north-northeast of Shark Bay, across the warm ochre hills of Western Australia's Pilbara Craton, geologists study the ancient Dresser and Strelley Pool formations. Few rocks on Earth are older or quieter."),
    (3, "Preserved within those Archean sedimentary beds stand fossilized conical, wavy, and domal stromatolites radiometrically dated between three point four three and three point four eight billion years old."),
    (5, "Rest quietly beside that almost unfathomable span of planetary time: molten young Earth had cooled enough to cradle stable liquid oceans scarcely a billion years earlier. Life wasted little time learning patience."),
    (5, "The primordial sky arching above those early Archean lagoons held virtually zero breathable free oxygen, glowing warm amber-copper through nitrogen, carbon dioxide, and water vapor."),
    (5, "A much closer young Moon raised broad, sweeping tides across shallow volcanic shelf seas, while a faster-spinning Earth completed each solar day in fewer than eighteen hours. Even the length of day was young."),
    (4, "Within those warm, quiet coastal shallows, ancestral cyanobacteria mats perfected the gentle alchemy of splitting abundant water molecules with sunlight and releasing tiny bubbles of free oxygen."),
    (4, "Lean close beside a shallow sunlit microbial mat in warm lagoon water today, and you can still watch delicate silver micro-bubbles of pure oxygen fizzing softly upward. Each tiny bubble carries ancient sunlight."),
    (5, "For more than a billion unhurried years, nearly every molecule of oxygen exhaled by Proterozoic stromatolite reefs dissolved into seawater and reacted quietly with dissolved ferrous iron."),
    (3, "Those patient underwater mineral reactions precipitated the world's immense banded iron formations across ancient seafloors long before surplus oxygen began accumulating in open air. Oceans cleared slowly before skies turned blue."),
    (5, "Then, around two point four billion years ago during the Great Oxidation Event, persistent stromatolite photosynthesis gradually endowed Earth with a protective ozone veil and breathable sky."),
    (7, "Every calm, effortless breath you draw into your lungs tonight is a living inheritance gifted by microscopic mats accreting millimeter-thin limestone beds across two billion quiet years. Ancient stillness made modern life possible."),
    (3, "High-magnification petrographic slices of ancient Proterozoic stromatolites even preserve delicate daily day-night growth laminae bundled gracefully into fortnightly tidal and annual solar cycles."),
    (7, "From those microscopic stone calendars, paleobiologists independently confirmed how tidal friction gently slowed Earth's spin from more than four hundred short days a year down to three hundred sixty-five. Living stone recorded astronomy itself."),
    (7, "Now gather all five peaceful chapters of Earth's Slowest Clocks, Volume Two side by side beneath warm evening candlelight."),
    (7, "We began eighty meters beneath North Atlantic swells, where five-hundred-year Arctica islandica clam shells archive annual ocean temperatures across more than thirteen calm centuries."),
    (7, "We journeyed to sheltered Lake Suigetsu beside the Sea of Japan, where fifty thousand yearly varves of pale diatoms and dark winter clay anchored humanity's radiocarbon calendar."),
    (7, "We drifted past sunlit coastal chalk cliffs, reading Earth's twenty-one-thousand-year precession and hundred-thousand-year orbital eccentricity pendulums written in marl and flint."),
    (7, "We descended three kilometers to volcanic mid-ocean ridges, tracing one hundred eighty million years of fingernail-paced seafloor spreading and magnetic pole reversals locked in basalt."),
    (3, "And tonight we rest beside three-point-five-billion-year stromatolites at Shark Bay—living stone clocks uniting microscopic patience with every breath of evening air. Five quiet archives complete one deep-time circle."),

    # Segment D (46..56): Series Finale Evening Wind-Down Under Shark Bay Starlight
    (8, "As warm Australian dusk fades into a serene, star-strewn night sky above Shark Bay, Hamelin Pool transforms into a dark, tranquil mirror reflecting the southern Milky Way."),
    (8, "All along the sheltered shallows, rounded stromatolite domes rest half-submerged in gentle tidal water, pausing their daytime photosynthesis in complete nocturnal stillness. Night water laps softly against warm limestone."),
    (6, "A soft, warm salt-flat breeze brushes quietly across white shell sand along the shore, while faint tidal ripples lap smoothly around ancient living stone."),
    (2, "Zero point three millimeters of growth a year never demanded notice on any single afternoon, yet across calm eons it transformed a barren rock world into a breathing home. Small faithful steps outlast every storm."),
    (8, "Across five centuries of ocean shells, fifty millennia of lake silt, a hundred millennia of chalk orbits, a hundred eighty million years of basalt, and three billion years of stromatolites, one lesson endures."),
    (7, "The natural universe accomplishes its deepest, most lasting work without haste, without clamor, and without ever rushing the quiet present moment."),
    (8, "Tonight, your resting body and quiet mind belong to that same unbroken continuum of natural time—cradled by ancient stone below and clear starlit air above. Every breath connects you to deep time."),
    (1, "Let the gentle wash of warm shallow lagoon water, soft salt wind, and faint oxygen bubble hush dissolve every remaining care of your waking day."),
    (8, "Allow your eyelids to grow comfortably heavy, breathing slowly in and slowly out in peaceful harmony with a calm night sea. Rest comes naturally when hurry falls away."),
    (8, "Nothing at all needs to be hurried tonight; Earth's slowest clocks keep faithful watch through the dark hours until gentle morning light returns."),
    (8, "Thank you for spending this calm, music-free journey with Earth's Slowest Clocks, Volume Two. May your sleep be deep, quiet, and restorative. Good night."),
]
