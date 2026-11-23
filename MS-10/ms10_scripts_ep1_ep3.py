#!/usr/bin/env python3
"""
MS-10 ("The Slow Night Train") — Episodes 1 to 3 Locked Scripts (ABR-AG-SOP-v2.1)
=================================================================================
Strict ABR-AG-SOP-v2.1 Spec:
- Continuous Master Voice Track (Stem 1) with 0 per-scene audio padding (`apad` forbidden)
- Decoupled visual holds (>= 15.0s net hold + 1.0s cross-dissolve overlaps across exact 901.00s / 15:01)
- Spoken Word Budget: strictly 1,650 - 1,850 words per 15-minute episode (110 - 120 WPM, >= 88% vocal duty)
- Zero ellipses (`...`), zero `[PAUSE >= 1.5s]` markers, zero background music, zero bells/chimes/lullabies.
"""

from __future__ import annotations

SCENE_DURATIONS_56_MS10: list[float] = (
    [17.0] * 6 + [18.0]
    + [15.75] * 8 + [16.0] * 9
    + [15.0, 15.0]
    + [15.75] * 16 + [16.0] * 3
    + [16.25] * 6 + [16.5] * 4 + [17.5]
)

assert len(SCENE_DURATIONS_56_MS10) == 56
assert round(sum(SCENE_DURATIONS_56_MS10), 2) == 901.00
assert min(SCENE_DURATIONS_56_MS10) >= 15.0

MS10_E01_LINES: list[tuple[int, str]] = [
    # Segment A (01..07): Arrival at Mossy Pine Station (00:00 - 02:00)
    (1, "Far up in the quiet folds of the evergreen valley, where the tall firs hold the evening mist like a soft grey shawl, sits a small wooden station made of weathered cedar planks."),
    (2, "Rain falls in thin, patient threads through the pine needles tonight, tapping gently along the mossy shingle roof and gathering in clear little droplets along the eaves above the sheltered platform."),
    (3, "No one hurries at Mossy Pine Station once twilight settles over the ridge, because the only train that visits after sunset is the Slow Night Train, and it never rushes a single mile."),
    (4, "Beneath the wide timber awning stands a warm brass oil lantern resting beside a curved oak bench, spreading a calm pool of amber light across the damp boards and shiny fern fronds."),
    (5, "Down the narrow iron rails, half veiled by curling wisps of pale valley fog, a gentle golden headlamp appears among the cedars, gliding forward no faster than a sleepy evening walk."),
    (6, "Welcome to The Slow Night Train, a quiet five-part bedtime journey through the rainy mountain valley, beginning tonight on the mossy cedar platform as the first carriage eases to a soft standstill."),
    (7, "With one low sigh of warm white steam rising into the cool pine air, the little wooden locomotive settles beside the platform, and its iron wheels rest calmly against the wet timber ties."),

    # Segment B (08..26): Boarding the Cedar Car & Meeting Conductor Barnaby (02:00 - 07:00)
    (8, "Out from the sheltered doorway of the first passenger carriage steps Conductor Barnaby, an elderly badger with neat silver stripes, round brass spectacles, and a heavy coat of soft moss-green wool."),
    (1, "Barnaby holds his dull brass lantern steady at his side so its warm amber flame never flickers too brightly, illuminating the three narrow cedar steps that lead up into the dry carriage."),
    (2, "Waiting politely at the edge of the oak bench is Pip, a small velvety brown dormouse wrapped snugly in a knitted ochre scarf, carrying a stitched linen satchel tucked neatly under one paw."),
    (3, "Good evening, young traveler, says Barnaby in a voice as soft and unhurried as rain on dry moss, and he lowers his paw gently to inspect Pip's tiny cream paper ticket stub."),
    (4, "Everything is in order for the Starlight Summit line, Barnaby nods with a warm smile, slipping the ticket back into Pip's front pocket before offering a steady paw up the wooden steps."),
    (5, "Pip climbs one cedar step, then the second, then the third, shaking three tiny raindrops from his whiskers before stepping across the woven wool doormat inside the quiet entryway."),
    (6, "At once, the cool damp scent of the mountain rain gives way to the deep, comforting fragrance of seasoned cedar paneling, clean wool blankets, and faint dried lavender tucked inside the seat cushions."),
    (7, "Behind Pip, Conductor Barnaby pulls the heavy sliding door shut with one smooth, muffled click of its brass latch, sealing out the chill breeze while leaving the soft patter of rain audible on the roof."),
    (8, "The passenger car holds only six wide window booths, each lined with deep burgundy and ochre quilted cushions, and every booth has its own small wall sconce glowing with calm amber light."),
    (1, "Pip walks slowly down the woven runner rug along the center aisle, feeling the soft pile beneath his boots while his eyes drift from one warm paneled wall to the next without any hurry."),
    (2, "Three booths ahead, an elderly hedgehog in a grey cardigan sits with his spectacles folded on his lap, already resting his chin gently against a plump feather pillow propped beside the dark window."),
    (3, "Across the aisle, two young field mice share a wide knitted quilt of oatmeal wool, their small ears tucked neatly beneath the hem as they listen to the steady rainfall tracing paths down the glass."),
    (4, "Barnaby gestures softly toward the fourth booth on the quiet mountain side of the carriage, where a freshly shaken wool blanket lies folded in a neat rectangle upon the cushioned bench."),
    (5, "This seat has the clearest view of the pine valley and the softest corner pillow in the whole car, Barnaby whispers, setting Pip's little linen satchel securely onto the brass luggage rack overhead."),
    (6, "Pip climbs up onto the quilted cushion and tucks his paws beneath his ochre scarf, noticing how the curved cedar backrest cradles his shoulders like the hollow of an old garden tree."),
    (7, "Before returning to the front vestibule, Barnaby checks the small iron radiator running beneath the windowsill, making sure a steady, gentle wave of dry warmth rises along the cool glass pane."),
    (8, "Up ahead in the cab of the little locomotive, Old Fern the silver-muzzled bear rests one broad paw upon the brass regulator handle, checking the low bed of glowing beechwood embers in the firebox."),
    (1, "Fern adds two dry split logs to the embers so the heat stays smooth and even, producing only a quiet crackle inside the iron hearth and a slow breath of pale steam from the chimney."),
    (2, "There is no sudden jolt and no loud clatter when the Slow Night Train begins to move; instead, the cedar carriage gives one tiny, comforting sway, like a wooden cradle nudged by a gentle breeze."),

    # Segment C (27..45): Gliding Through the Rainy Pine Valley (07:00 - 12:00)
    (3, "Outside Pip's arched window, the mossy cedar platform of the station drifts slowly backward into the rainy twilight, its lone brass bench lantern shrinking into a soft amber speck among the ferns."),
    (4, "Soon the tall valley pines draw close on either side of the narrow track, their wet green boughs bowing quietly under the evening drizzle while ribbons of cool mist weave between the dark trunks."),
    (5, "Pip presses two small paws lightly against the wooden sill and watches the raindrops gather at the top of the glass, roll down in patient silver trails, and join together near the brass frame."),
    (6, "Beneath the woven rug of the carriage floor, the iron wheels find their calm evening cadence across the timber ties, a low, steady, muffled pulse that feels almost like a slow heartbeat."),
    (7, "Every few yards, the cedar walls give a soft, reassuring timber creak as the track bends gently around a mossy boulder or follows the winding bank of a shallow mountain creek."),
    (8, "Pip opens his tiny stitched linen satchel and takes out his favorite travel keepsake, a single dried cedar leaf pressed flat inside a folded square of soft cream parchment."),
    (1, "He lays the pressed leaf gently on the small wooden window table beside his paws, admiring the fine pale veins that look just like the branching mountain trails outside in the mist."),
    (2, "Across the carriage, the small oil sconces sway barely a fraction of an inch with the curve of the track, painting long, slow amber shadows across the curved ceiling ribs overhead."),
    (3, "Pip notices how different tonight feels from a busy daytime journey, because there are no bright signs flashing past the glass and no crowded voices hurrying down the narrow aisle."),
    (4, "Everything inside the cedar car moves at the speed of settling rainwater and slow breathing, giving his eyes plenty of time to rest upon each quiet silhouette of pine and fern outside."),
    (5, "Along a clearing beside the tracks, a family of tawny deer stands sheltered beneath an old spruce tree, their ears turning calmly as the warm amber windows glide past without disturbing their rest."),
    (6, "A little farther up the valley, the train passes an old stone footbridge covered in velvet moss, where clear rainwater trickles smoothly down the boulders into the dark creek below."),
    (7, "Pip draws the folded wool blanket up over his knees and feels its soft brushed nap warming his toes, while the gentle radiator heat rises in a quiet curtain beside the glass."),
    (8, "Down at the far end of the carriage, Conductor Barnaby walks slowly along the aisle with a clean linen cloth, pausing to wipe a tiny bead of evening mist from the brass doorknob."),
    (1, "He nods warmly to Pip as he passes, adjusting his round spectacles before stepping smoothly through the cushioned doorway toward the next carriage along the train."),
    (2, "For a moment, as that doorway opens and closes again with a soft wooden click, a wonderfully comforting aroma drifts gently down the length of the cedar aisle."),
    (3, "It smells of warm dried chamomile blossoms, toasted barley grains, and clean steam rising from a heavy brass kettle kept simmering on a quiet iron stove."),
    (4, "Pip takes a slow, deep breath through his nose, feeling his shoulders sink a little deeper into the quilted burgundy cushion as that cozy scent settles around his booth."),
    (5, "Outside the window, the rain has softened even further into a fine mountain drizzle, turning the dark pine ridges into layered washes of twilight slate and misty grey-green."),

    # Segment D (46..56): Evening Wind-Down & Forward Bridge to Episode 2 (12:00 - 15:00)
    (6, "Inside the carriage, the elderly hedgehog across the way breathes slowly and evenly in his corner seat, and the two young field mice have already drifted into peaceful evening rest."),
    (7, "Pip folds his pressed cedar leaf carefully back inside its cream parchment square and tucks it safely into his linen satchel, resting his cheek gently against the soft woven pillow."),
    (8, "The low cadence of the wooden carriage beneath him grows even steadier now, carrying him forward through the quiet valley without a single sudden sound or hurried turn."),
    (1, "Raindrops continue their patient, unhurried descent along the dark glass, each tiny bead catching a faint glint of warm amber from the wall sconce before slipping softly out of sight."),
    (2, "You can let your own breathing match that calm, even pace tonight, drawing air in slowly as the carriage glides along the pines, and letting every thought of the day settle softly downward."),
    (3, "There is nowhere left to hurry and nothing left to finish before morning arrives; the cedar walls are warm, the wool blanket is tucked snug, and the mountain night holds everything safely."),
    (4, "Every mile along this quiet valley track is watched over with patience by Old Fern at the firebox and Conductor Barnaby along the aisle, keeping the journey smooth from dusk until dawn."),
    (5, "Down the narrow paneled corridor ahead, the warm glow of the next carriage shines gently through a frosted glass window, inviting Pip to stretch his paws for one quiet evening visit."),
    (6, "As the Slow Night Train rolls steadily deeper into the misty pine hills, that comforting scent of steeped chamomile and warm roasted barley drifts softly through the cedar doorway once more."),
    (7, "In Episode Two of The Slow Night Train, Pip steps gently down the quiet corridor into Mrs. Wren's cozy timber dining car, where a dull brass teapot steams softly beside rain-streaked glass."),
    (8, "For now, keep your eyes soft and your shoulders resting easily against the pillow, listening to the gentle mountain rain and the calm wooden sway of the train as night settles peacefully around you."),
]

MS10_E02_LINES: list[tuple[int, str]] = [
    # Segment A (01..07): Arrival in the Quiet Dining Car (00:00 - 02:00)
    (1, "Steady evening rain glides down the arched windows of the Slow Night Train as the little wooden carriages follow the gentle curve of the misty evergreen valley."),
    (2, "Inside the first passenger car, Pip the dormouse untucks his paws from his warm wool blanket, adjusts his knitted ochre scarf, and steps softly down onto the woven aisle rug."),
    (3, "Guided by the comforting aroma of steeped chamomile blossoms and toasted barley, Pip walks unhurriedly toward the paneled cedar door at the front end of the carriage."),
    (4, "He presses the dull brass latch gently downward and passes across the covered timber gangway, where cool mountain air brushes his whiskers for just one quiet second before the next door opens."),
    (5, "Welcome back to The Slow Night Train, Episode Two, stepping tonight into the warm amber glow of the quiet dining car, where Mrs. Wren keeps her heavy brass teapot simmering softly."),
    (6, "Unlike a noisy daytime dining hall, this narrow wooden carriage feels like a tucked-away cottage kitchen on wheels, lit only by small low-hanging oil sconces and the soft gleam of polished mahogany."),
    (7, "Four cozy cedar booths line the rain-streaked windows on each side, with clean cream linen cloths smoothed neatly over every tabletop and woven wool runners quieting every footstep along the floor."),

    # Segment B (08..26): Mrs. Wren & The Craft of Evening Tea (02:00 - 07:00)
    (8, "Behind a low timber counter at the far end of the car stands Mrs. Wren, a round speckled winter wren wearing a crisp cream linen apron stitched along the hem with tiny brown leaf patterns."),
    (1, "Beside her rests a small cast-iron warming stove fueled by smooth glowing embers of dry alder wood, giving off a soft, steady crackle and a gentle blanket of kitchen warmth."),
    (2, "Come right in, Pip, says Mrs. Wren in a voice as soft and unhurried as steam rising from a warm bowl, and she motions gently toward the corner booth nearest the stove."),
    (3, "Pip climbs up onto the quilted patchwork cushion of the booth, resting his chin just high enough to watch Mrs. Wren's patient, methodical movements behind the cedar counter."),
    (4, "On the iron stovetop sits a rounded, dull brass teapot whose handle is wrapped snugly in braided hemp twine so it always stays comfortable and safe to hold."),
    (5, "A thin, pale curl of steam lifts gently from the curved spout, drifting upward into the amber lantern light before vanishing softly against the curved cedar ribs of the ceiling."),
    (6, "Tonight I have steeped wild valley chamomile with a pinch of dried lemon balm and roasted barley grain, Mrs. Wren explains softly, lifting the wooden lid of a small stoneware caddy."),
    (7, "She measures two neat wooden spoonfuls of golden dried blossoms into a warm clay strainer, letting the clean, earthy fragrance of summer meadows unfold gently through the rainy evening air."),
    (8, "Next, she lifts the heavy brass teapot with both wings and pours a slow, steady stream of hot spring water over the blossoms, filling the small stoneware pot with pale amber tea."),
    (1, "Nothing about Mrs. Wren's tea making is ever rushed; she sets a tiny sandglass beside the pot and watches the fine cream grains trickle steadily from the top bulb into the bottom."),
    (2, "While the tea steeps in quiet stillness, Pip rests his paws flat on the warm linen tablecloth and watches the mountain rain draw long silver lines down the dark arched windowpane."),
    (3, "Outside in the twilight slate mist, tall spruce branches lean close to the track and brush lightly past the roof eaves, leaving tiny fresh beads of rainwater glistening on the glass."),
    (4, "Mrs. Wren opens a wooden breadbox lined with folded beeswax cloth and takes out two small, round oatcakes baked earlier that afternoon with a hint of clover honey and crushed fennel seed."),
    (5, "She places the warm oatcakes onto a pale stoneware saucer, sets a thick ceramic mug beside them, and carries the small wooden tray unhurriedly down the woven rug to Pip's booth."),
    (6, "Setting the tray gently down on the linen cloth, she tilts the dull brass teapot so a thin, golden ribbon of chamomile tea fills Pip's mug without a single splash."),
    (7, "Wait just three calm breaths for the steam to soften, she advises kindly, tucking a folded corner of the patchwork blanket warmly over Pip's knees before taking a seat across the table."),
    (8, "Mrs. Wren pours a tiny thimble-sized cup of barley tea for herself, folding her speckled wings comfortably around the warm clay while the wooden carriage rocks in its slow, even rhythm."),
    (1, "Pip wraps both small paws around his ceramic mug, feeling the deep, steady warmth soak straight through his fur and soften the last trace of evening chill from the station platform."),
    (2, "He takes one careful, quiet sip, tasting the mild floral sweetness of meadow chamomile followed by the nutty, comforting warmth of roasted barley grain."),

    # Segment C (27..45): Quiet Stories Inside the Rainy Carriage (07:00 - 12:00)
    (3, "Across the aisle, the dining car remains hushed and peaceful; only one other traveler sits near the rear window, a gentle barn owl in a knitted grey shawl slowly turning pages of a botanical sketchbook."),
    (4, "Every now and then, the owl pauses to gaze out at the misty pine ridges, letting the quiet darkness rest his eyes before turning another thick cream page with barely a whisper."),
    (5, "Mrs. Wren tells Pip softly about how she gathers her chamomile blossoms during the warm, unhurried afternoons of late July along the sunny gravel banks beside the lower valley creek."),
    (6, "She dries the little white-and-gold flowers slowly on woven willow trays inside her cottage attic, turning them gently each morning until they hold the soft scent of dry summer grass."),
    (7, "That way, whenever autumn rain or winter mist sweeps across the mountain rails, every traveler aboard the Slow Night Train can taste a quiet spoonful of warm meadow sunlight before sleep."),
    (8, "Pip nibbles a tiny corner of his honey oatcake, noticing how crisp and mild it tastes alongside a second slow sip of chamomile tea, while the alder stove crackles softly behind the counter."),
    (1, "Down beneath the mahogany floorboards, the iron wheels continue their low, muffled cadence over the wet timber ties, never speeding up on the straightaways and never jostling on the bends."),
    (2, "A soft tap of rain against the upper windowpane draws Pip's gaze outward, where a pale patch of twilight sky shows between drifting valley clouds and outlines the dark ridge of cedar trees."),
    (3, "Conductor Barnaby steps quietly through the rear doorway for a brief check of the oil sconces, adjusting one brass wick a hair lower so the dining car glow stays soft and amber."),
    (4, "Evening, Mrs. Wren, and evening again, young Pip, Barnaby murmurs warmly, accepting a small ceramic cup of roasted barley tea to warm his paws before his next walk down the corridor."),
    (5, "Old Fern says the mist is lying thick and white along the deep river gorge tonight, Barnaby adds softly, so we will take the old stone viaduct at half pace for an extra smooth crossing."),
    (6, "Mrs. Wren nods approvingly, knowing how much the sleepy passengers enjoy that quiet glide high above the misty treetops, where the train feels almost as if it is floating through soft clouds."),
    (7, "After finishing his warm cup, Barnaby sets it neatly on the wooden counter, tips his moss-green cap kindly, and slips back out into the hushed vestibule with one gentle click of the latch."),
    (8, "Pip finishes the last warm sip of his chamomile tea and sets his ceramic mug cleanly upon the stoneware saucer, feeling a heavy, pleasant drowsiness beginning to settle behind his eyelids."),
    (1, "Mrs. Wren clears the little tray without a single clink of crockery, wrapping the remaining oatcake crumb neatly in beeswax cloth and wiping the linen cloth smooth with a soft wing."),
    (2, "She banks the embers inside the cast-iron warming stove beneath a thin layer of clean grey ash so the dining car will stay evenly warm all through the sleeping hours ahead."),
    (3, "Then she dims the front counter lantern down to a tiny amber bead, leaving only the cozy booth sconces glowing warmly against the polished cedar woodwork."),
    (4, "Pip slides gently back into the corner of the quilted patchwork booth, resting his ochre scarf beneath his cheek while the quiet warmth of the tea spreads all the way to his toes."),
    (5, "Outside the rain-streaked glass, the dense pine forest begins to open gradually along the mountain shelf, revealing the pale ribbon of valley mist waiting just ahead in the cool night air."),

    # Segment D (46..56): Evening Wind-Down & Forward Bridge to Episode 3 (12:00 - 15:00)
    (6, "Inside the dining car, the barn owl closes his botanical sketchbook softly, ties its linen ribbon with steady calm, and leans back against his quilted headrest to rest."),
    (7, "The heavy brass teapot sits quiet and cool upon the iron hob now, its thin wisp of steam folded gently back into the warm cedar air of the silent kitchen."),
    (8, "Everything around Pip feels slow, soft, and comfortably heavy, from the brushed wool blanket tucked over his paws to the low, steady sway of the wooden carriage beneath his seat."),
    (1, "Notice how calm the room around you feels right now, as if a warm ceramic cup of evening tea has eased every hurried corner of the day away into quiet stillness."),
    (2, "Let your shoulders drop gently into the mattress and let your breath move in and out at the same unhurried rhythm as the soft rain sliding down the dark windowpane."),
    (3, "There are no errands waiting in the hallway and no bright lights asking for your attention; only warm amber shadows, soft wool, and the steady patience of the night."),
    (4, "Up ahead in the engine cab, Old Fern eases the brass regulator back a notch as the valley floor opens wide beneath the tracks, guiding the wooden train toward the mossy arches of the ridge."),
    (5, "Pip blinks slowly and lifts his gaze toward the arched windowpane, watching the pale silver mist curl gently upward between the dark tips of the tall valley pines."),
    (6, "Beneath the wheels, the muted timber cadence softens into a deep, resonant hush as the narrow rails pass from earthy hillside onto solid carved mountain stone."),
    (7, "In Episode Three of The Slow Night Train, the warm cedar carriages glide slowly out across the ancient stone viaduct, floating calmly high above the quiet mist-filled river valley."),
    (8, "Until that gentle crossing unfolds, let your eyelids grow comfortably heavy, resting inside the warm cedar quiet as the Slow Night Train carries you smoothly into sleep."),
]

MS10_E03_LINES: list[tuple[int, str]] = [
    # Segment A (01..07): Approaching the Stone Viaduct (00:00 - 02:00)
    (1, "High along the winding shoulder of the evergreen ridge, the evening rain tapers into a cool, velvety mountain mist that settles softly between the tall dark spruces."),
    (2, "Gliding out from the shelter of the pine trees comes the Slow Night Train, its three warm cedar carriages glowing like gentle amber lanterns against the twilight slate sky."),
    (3, "Up in the quiet locomotive cab, Old Fern the silver-muzzled bear eases the brass lever smoothly back, slowing the iron wheels to the calmest, most unhurried pace of the entire journey."),
    (4, "Ahead of the engine stretches the old mossy stone viaduct, seven wide rounded arches carved centuries ago from pale river granite and built to span the deep quiet gorge from ridge to ridge."),
    (5, "Welcome to Episode Three of The Slow Night Train, drifting calmly tonight across the ancient stone viaduct high above the mist valley, with zero music and only the quiet hush of the hills."),
    (6, "Inside the cozy window booth, Pip the dormouse sits tucked beneath his patchwork wool quilt, resting his chin upon his folded paws as the dark pine boughs part smoothly outside the glass."),
    (7, "All at once, the view beyond the arched window opens into a wide, tranquil sea of pale silver mist, filling the valley floor below like a soft blanket of combed sheep's wool."),

    # Segment B (08..26): Floating Across the Seven Mossy Arches (02:00 - 07:00)
    (8, "Beneath the cedar carriage floor, the sound of the tracks changes subtly as the rails pass onto solid mountain granite, turning into a deep, muffled, steady whisper."),
    (1, "Far below the seven stone arches, a wide shallow river winds patiently over rounded grey pebbles, its distant murmur rising faintly through the mist like a soft breath in the night."),
    (2, "Above the ridge, the evening clouds drift slowly apart just enough to reveal a pale, misty crescent moon, pouring quiet silver-grey light across the drifting fog banks."),
    (3, "Pip watches wisps of pale white steam curl lazily backward from the little locomotive chimney, blending smoothly into the valley clouds until it is hard to tell steam from mist."),
    (4, "Along the stone parapet just outside the window, thick cushions of velvet green moss and tiny curled mountain ferns grow safely between the weathered granite blocks."),
    (5, "Conductor Barnaby pauses quietly beside Pip's booth, adjusting his round brass spectacles as he gazes out across the tranquil mist valley with the fondness of someone who has crossed it a thousand nights."),
    (6, "Every stone in these seven arches was fitted by hand without mortar rushing to dry, Barnaby says in a calm whisper, so the bridge settles more peacefully into the valley with every passing year."),
    (7, "He points gently downward toward the second arch, where the tall tips of ancient valley cedars poke softly through the pale fog like dark green islands resting in a calm silver sea."),
    (8, "Look closely at the tallest cedar branch, Barnaby adds softly, and Pip spots a pair of quiet wood owls perched side by side in the dry shelter beneath the upper boughs, resting without a stir."),
    (1, "Because the Slow Night Train never blows a sharp whistle or clatters quickly across the stone, the valley wildlife knows its warm amber windows simply mean that bedtime has arrived."),
    (2, "Down on the mossy ledge of the third granite pier, a small red fox lies curled neatly into a warm copper circle with his bushy tail wrapped snugly over his nose, untouched by the passing glow."),
    (3, "Inside the cedar carriage, the little oil sconces burn steadily inside their glass chimneys, casting a calm honey-colored light over the carved wooden paneling and woven wool blankets."),
    (4, "Pip leans his forehead gently against the cool corner of the window frame, feeling the faint, reassuring vibration of the slow timber wheels traveling smoothly across the fourth stone arch."),
    (5, "Here at the very center of the viaduct, the valley stretches out wide and quiet on both sides, with layered blue-grey mountain ridges fading gently into the soft night horizon."),
    (6, "No lantern burns in any distant farmhouse down in the hollow tonight, for every valley cottage has already banked its hearth embers and drawn its linen curtains closed for sleep."),
    (7, "Only the soft moonlit mist moves slowly along the river course below, curling around smooth willow banks and drifting over mossy stones without a single hurried ripple."),
    (8, "Barnaby reaches gently into his moss-green wool coat pocket and hands Pip a small smooth river pebble worn flat and velvety by a hundred quiet winters in the valley stream."),
    (1, "Keep this warm in your paw while we cross the last three arches, Barnaby says kindly, for nothing feels calmer at bedtime than holding a smooth stone warmed by your own quiet hand."),
    (2, "Pip curls his tiny paws around the silky grey pebble, feeling its cool smooth surface gradually warm to match the gentle heat of his fur beneath the patchwork quilt."),

    # Segment C (27..45): The Far Ridge & The Quiet Pine Breeze (07:00 - 12:00)
    (3, "As the Slow Night Train glides calmly onto the fifth granite arch, a soft mountain breeze drifts across the viaduct, carrying the clean, resinous fragrance of damp pine bark and cool stone."),
    (4, "Through the tiny brass ventilation slit near the curved carriage ceiling, just a whisper of that crisp evening air enters the warm cedar room, keeping the air fresh and easy to breathe."),
    (5, "Pip closes his eyes for three unhurried breaths, listening to the gentle layers of sound around him: the distant valley river far below, the soft pine breeze outside, and the slow timber sway."),
    (6, "When he opens his eyes again, the train is passing smoothly over the sixth stone arch, where tendrils of silvery cloud drift right past the lower edge of the wooden windowpane."),
    (7, "For a peaceful moment, the cedar carriage feels as though it has left the ground altogether, sailing smoothly through a soft cushion of moonlit mist high above the sleeping forest."),
    (8, "Up ahead in the engine cab, Old Fern glances back along the curved line of glowing amber windows, smiling softly to see how steady and tranquil every single carriage rides behind him."),
    (1, "He checks the warm brass water gauge by the low glow of the firebox, ensuring the boiler holds an even, gentle pressure for the easy climb up the far mountain foothills."),
    (2, "Across the aisle from Pip, the elderly hedgehog has tucked his paws completely under his grey cardigan, resting in deep, undisturbed slumber while the soft carriage rocks him gently."),
    (3, "Down the corridor in the dining car, Mrs. Wren has already finished tidying her stoneware mugs, leaving only a single dimmed lantern glowing warmly above the clean mahogany counter."),
    (4, "Gradually, the seventh and final stone arch carries the wooden locomotive back onto the mossy earth of the eastern ridge, where tall hemlock trees welcome the tracks back into quiet shelter."),
    (5, "The deep granite hush beneath the wheels softens back into the familiar, comforting murmur of iron gliding steadily over cedar ties cushioned in damp pine needles."),
    (6, "Beside the rails, lush banks of mountain heather and soft green bracken lean gently beneath the evening dew, glistening faintly whenever the warm carriage windows pass quietly by."),
    (7, "Pip tucks Barnaby's smooth river pebble safely beside his pressed cedar leaf inside his linen satchel, feeling a deep, quiet gratitude for how gentle the valley crossing had been."),
    (8, "Looking back through the rear corner of the arched window, he can still glimpse the curved stone viaduct resting peacefully across the pale mist behind them, bathed in soft crescent moonlight."),
    (1, "Ahead of the train, the narrow track winds calmly along a sheltered hillside where small stone cottages with mossy chimneys sit tucked among old apple orchards and quiet terraced gardens."),
    (2, "Even though those mountain villages are already fast asleep beneath their slate roofs, the Slow Night Train carries something thoughtful and quiet for their morning doorsteps."),
    (3, "Just behind the passenger carriage sits the warm cedar mail car, lined from floor to ceiling with tidy wooden cubbies filled with twine-tied parcels and cream parchment envelopes."),
    (4, "Through the frosted glass of the rear vestibule door, Pip notices a soft amber lantern swaying gently as Conductor Barnaby prepares to sort the evening post for the hillside stops."),
    (5, "The quiet rustle of brown wrapping paper and soft linen mailbags blends seamlessly into the steady cadence of the wooden carriage as the train climbs slowly into the quiet foothills."),

    # Segment D (46..56): Evening Wind-Down & Forward Bridge to Episode 4 (12:00 - 15:00)
    (6, "Inside Pip's booth, the warmth from the iron radiator wraps around his quilted seat like a quiet evening hearth, and his eyelids blink slower and slower with each passing pine tree."),
    (7, "Outside the glass, the pale crescent moon drifts calmly behind a thin ribbon of silver cloud, softening the twilight hillside into muted shades of mossy green and deep indigo."),
    (8, "Every tree, every boulder, and every smooth pebble down in the mist valley rests undisturbed beneath the same quiet sky that watches over your own bedroom window tonight."),
    (1, "Let your body grow just as heavy and relaxed as a smooth granite arch resting firmly in the quiet earth, supported completely so you do not have to hold up a single muscle."),
    (2, "Breathe in slowly and calmly, imagining the clean, cool scent of mountain pines after evening rain, and breathe out softly, letting the last busy thoughts of the day drift away like valley mist."),
    (3, "There is no hurry in the hills tonight; the stone bridge has been crossed smoothly, the warm cedar walls hold the quiet close, and the wheels turn at an easy, unhurried pace."),
    (4, "Down the narrow wooden corridor behind Pip's booth, Conductor Barnaby adjusts his round brass spectacles and lifts a soft linen bundle of mountain village parcels onto his sorting table."),
    (5, "Each little package holds something humble and kind for morning, from knitted wool mittens and jars of clover honey to pressed mountain wildflowers wrapped in clean cream twine."),
    (6, "As the Slow Night Train glides peacefully along the sleeping hillside toward its quiet midnight stops, Pip feels curious enough for one more calm visit before climbing into his berth."),
    (7, "In Episode Four of The Slow Night Train, we step softly into the cozy cedar mail car with Conductor Barnaby as he sorts and sets down quiet parcels for the sleeping mountain villages."),
    (8, "For tonight, settle deeper beneath your warm blanket, keep your breath slow and steady, and let the hushed sway of the wooden train carry you gently toward peaceful rest."),
]
