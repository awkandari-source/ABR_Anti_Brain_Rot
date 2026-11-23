#!/usr/bin/env python3
"""
MS-10 ("The Slow Night Train") — Episodes 4 and 5 Locked Scripts (ABR-AG-SOP-v2.1)
===================================================================================
Strict ABR-AG-SOP-v2.1 Spec:
- Continuous Master Voice Track (Stem 1) with 0 per-scene audio padding (`apad` forbidden)
- Decoupled visual holds (>= 15.0s net hold + 1.0s cross-dissolve overlaps across exact 901.00s / 15:01)
- Spoken Word Budget: strictly 1,650 - 1,850 words per 15-minute episode (110 - 120 WPM, >= 88% vocal duty)
- Zero ellipses (`...`), zero `[PAUSE >= 1.5s]` markers, zero background music, zero bells/chimes/lullabies.
"""

from __future__ import annotations

MS10_E04_LINES: list[tuple[int, str]] = [
    # Segment A (01..07): Entering the Cozy Cedar Mail Car (00:00 - 02:00)
    (1, "Higher along the quiet mountain foothills, the evening rain has turned into the softest, slowest drift of early winter snowflakes, floating past the dark pine boughs without making a sound."),
    (2, "The Slow Night Train climbs smoothly along the sheltered hillside track, its warm amber windows casting gentle honey-colored ribbons across the dusted evergreen branches and mossy roadside boulders."),
    (3, "Just behind the quiet passenger carriage sits the cedar mail car, a cozy timber room filled with the comforting scents of brown craft paper, beeswax string, dry cedar wood, and clean linen sacks."),
    (4, "Pip the dormouse eases the cushioned rear door open just wide enough to slip inside, shutting it gently behind him with one soft click so no mountain draft enters the warm room."),
    (5, "Welcome back to The Slow Night Train, Episode Four, stepping tonight into the sleepy mail car where Conductor Barnaby prepares quiet evening parcels for the mountain villages resting along the ridge."),
    (6, "From the curved wooden ceiling hangs a single dull brass oil lantern, shedding a calm amber circle over tall rows of tidy cedar cubbies built along the entire inner wall."),
    (7, "Every cubby holds neat bundles of cream envelopes tied with soft hemp twine, small square brown parcels, and plump woven mailbags waiting patiently for their hillside stops."),

    # Segment B (08..26): Sorting Parcels Under the Hanging Lantern (02:00 - 07:00)
    (8, "Seated at a smooth oak sorting desk beside the frosted window is Conductor Barnaby, his round brass spectacles resting low on his nose as his paws fold a corner of crisp brown paper with unhurried care."),
    (1, "Ah, good evening again, young Pip, Barnaby murmurs warmly without rushing a single knot, and he gestures kindly toward a wide cedar bench covered with a thick folded plaid wool blanket."),
    (2, "Climb right up onto the folded blanket if you like, Barnaby whispers, because sorting the hillside post is the calmest chore on the whole line and makes fine quiet company before sleep."),
    (3, "Pip climbs up onto the soft plaid wool, tucks his small paws neatly beneath his knitted ochre scarf, and rests his chin on the warm wooden armrest where he can watch Barnaby work."),
    (4, "Outside the square timber windowpane, tiny white snowflakes drift down in slow diagonal lines against the twilight indigo slope, settling gently onto the broad needles of the hillside firs."),
    (5, "On the sorting desk sits a spool of pale flax twine, a small cedar handle for stamping soft wax seals, and a little ceramic dish holding smooth beads of amber pine resin."),
    (6, "Barnaby picks up the first small parcel wrapped in clean brown paper, reads its neat handwritten tag beneath the warm lantern light, and checks that the twine bow sits flat and secure."),
    (7, "This little box belongs to the weaver's cottage at Alder Bend, Barnaby explains softly, holding two skeins of dyed autumn wool spun down in the valley so she can finish her winter blankets tomorrow."),
    (8, "He places the parcel gently inside the upper left linen sack, where the soft woven cloth cushions every corner so nothing shifts or bumps while the wooden carriage glides along the rails."),
    (1, "Next, Barnaby lifts a flat cream parcel tied neatly with sage-green ribbon, turning it once in his paws to smooth a tiny crease along the folded brown paper edge."),
    (2, "Inside this one rest pressed botanical sketches and a packet of sweet pea seeds traveling up to the schoolhouse at Fern Hollow, ready to wait safely in a cedar drawer until spring thaw."),
    (3, "Every movement Barnaby makes is deliberate, unhurried, and quiet: the soft whisper of paper folding, the light pull of flax twine, and the gentle set of each bundle into its waiting cubby."),
    (4, "Pip watches the steady rise and fall of Barnaby's moss-green wool sleeves beneath the warm lantern glow, noticing how calming it feels simply to watch careful hands finish a gentle task."),
    (5, "Beneath the timber floor of the mail car, the iron wheels keep their low, even cadence across the hillside ties, rocking the hanging oil lantern only a whisper from side to side."),
    (6, "Barnaby reaches into the third row of cedar cubbies and draws out a round wooden canister wrapped in beeswax cloth, smelling faintly of toasted hazelnuts and wild mountain clover honey."),
    (7, "Grandmother Squirrel at Willow Ridge sent this down for her cousins at Cedar Crossing, Barnaby smiles softly, tucking the round canister snugly into a padded wool pouch inside the second mailbag."),
    (8, "There are no urgent telegrams and no hurried daytime invoices aboard the Slow Night Train; every single envelope and parcel carries something warm, patient, or kind for a quiet morning ahead."),
    (1, "One by one, Barnaby checks off the hillside stops inside his small leather ledger using a blunt graphite pencil that makes only the softest, hushed scratch across the thick cream page."),
    (2, "As the last parcel settles neatly inside the Alder Bend mailbag, the wooden carriage gives a faint, gentle sigh of slowing steam from the little locomotive up ahead in the snow."),

    # Segment C (27..45): Quiet Village Stops Along the Sleeping Ridge (07:00 - 12:00)
    (3, "Outside the window, the dark pine forest parts around a tiny wooden post platform lit by one sheltered amber oil lamp, with the dark slate rooftops of Alder Bend resting silently beyond the fence."),
    (4, "Not a single cottage window is lit in the sleeping village, because every family has long since tucked beneath their winter quilts, trusting the Slow Night Train to leave their morning post quietly."),
    (5, "Old Fern brings the little locomotive to a smooth, feather-light pause beside the cedar mail post without a single jolt or loud hiss, letting the falling snow settle calmly around the wheels."),
    (6, "Barnaby pulls his moss-green wool collar neatly up around his ears, lifts the first soft linen mailbag by its braided handle, and slides the wide cedar side door open just a narrow space."),
    (7, "A crisp, clean breath of snowy mountain pine air drifts into the mail car for three quiet seconds as Barnaby steps down onto the dusted wooden step and sets the linen bag inside the sheltered post box."),
    (8, "He lowers the wooden lid of the post box gently so it closes without a sound, checks that the little rain latch sits snug, and climbs smoothly back inside the warm cedar carriage."),
    (1, "With one muted slide of the timber door, the snowy hillside stillness returns outside the glass, and the warm lantern glow wraps right back around Pip on his folded wool blanket."),
    (2, "Up in the cab, Old Fern eases the brass regulator open barely a hair, and the wooden train glides softly away from Alder Bend, climbing calmly along the quiet curved shelf toward Fern Hollow."),
    (3, "Pip curls his toes deeper into the warm plaid wool, his eyelids drooping halfway as he watches the tiny snowflakes touch the warm outer glass and melt slowly into clear little beads."),
    (4, "Barnaby returns to his oak sorting desk, sets his spectacles gently beside the leather ledger for a moment, and warms his paws softly near the brass chimney of the hanging lantern."),
    (5, "Ten quiet minutes later, the train pauses with the same unhurried grace beside the snow-dusted cedar post at Fern Hollow, where the second linen mailbag is tucked safely inside its dry wooden chest."),
    (6, "Near the edge of the snowy fence, a small brown snowshoe hare sits motionless in the shelter of a spruce root, watching the warm amber windows with calm dark eyes as the train moves smoothly on."),
    (7, "Back inside the mail car, the tall rows of cedar cubbies are nearly empty now, leaving only smooth polished woodwork, a neat coil of flax twine, and one final cream parcel waiting on the oak desk."),
    (8, "Barnaby picks up that last small bundle tied with soft ochre yarn, smiling gently as he glances over at Pip resting peacefully on the folded plaid wool blanket."),
    (1, "This last little parcel goes all the way to the stationmaster's cabin at Starlight Summit, Barnaby whispers softly, holding fresh woolen socks and a tin of dried mountain mint leaves for morning tea."),
    (2, "He sets the final bundle cleanly inside the last linen pouch and hangs the pouch on its brass hook beside the door, then closes his leather ledger with one soft, unhurried pat."),
    (3, "All the evening sorting is finished now, and the cedar mail car grows even quieter than before, holding only the gentle creak of seasoned timber and the steady, muffled rhythm of the slow climb."),
    (4, "Outside the arched glass, the snowy pine trees grow slightly shorter and wider apart as the narrow track nears the peaceful high clearing of Starlight Summit under the pale night sky."),
    (5, "Barnaby dims the desk lamp down to a warm amber ember, leaving just enough soft honey light to guide Pip gently back through the corridor toward the quiet sleeping berths at the front of the car."),

    # Segment D (46..56): Evening Wind-Down & Forward Bridge to Episode 5 (12:00 - 15:00)
    (6, "Pip stretches his small paws softly against the plaid wool blanket, feeling wonderfully heavy and drowsy now that every hillside parcel has found its quiet home for the night."),
    (7, "Barnaby lifts Pip's little stitched linen satchel gently onto his arm and offers a warm, steady paw, guiding him unhurriedly through the cushioned doorway toward the quiet sleeping compartment."),
    (8, "Everything aboard the Slow Night Train is settling down for the deepest hours of rest; the dining car is dark and warm, the mail cubbies are tidy, and the snow falls softly over the hills."),
    (1, "You can let your own mind grow just as tidy and calm tonight, setting every worry or unfinished plan neatly inside a quiet wooden cubby where it can wait safely until morning light."),
    (2, "There are no more messages to sort and no more doors to open; just the soft weight of your warm blanket, the calm rhythm of your breath, and the gentle hush of falling mountain snow."),
    (3, "Up ahead in the little locomotive cab, Old Fern banks the beechwood embers low and steady, guiding the warm cedar carriages smoothly along the last gentle bend toward the high summit clearing."),
    (4, "Through the narrow window beside the corridor, the evening clouds begin to thin above the tall white pines, revealing the first calm pinpoints of pale silver starlight overhead."),
    (5, "Waiting just behind the next paneled cedar door is Pip's own cozy sleeping berth, already made up with a thick patchwork wool quilt, a plump feather pillow, and a tiny dimmed amber bedside lamp."),
    (6, "Barnaby pauses gently beside the compartment doorway, turning the smooth brass handle without a single click so the quiet room inside stays completely undisturbed."),
    (7, "In Episode Five, the peaceful finale of The Slow Night Train, Pip climbs beneath his patchwork wool quilt at Starlight Summit as the quiet wooden train comes to rest beneath the pines."),
    (8, "Until those final serene miles unfold, keep your breath slow, soft, and steady, resting deeply inside the warm wooden stillness of the quiet night."),
]

MS10_E05_LINES: list[tuple[int, str]] = [
    # Segment A (01..07): Arriving at the Quiet Sleeping Compartment (00:00 - 02:00)
    (1, "High above the misted evergreen valley, where the mountain air grows crisp, still, and clear beneath a wide canopy of pale silver stars, the Slow Night Train glides along its final gentle curve."),
    (2, "Soft white snow rests untouched upon the broad boughs of the alpine pines outside the arched windows, glowing faintly beneath the calm crescent moon as the last drifting clouds part silently overhead."),
    (3, "Inside the warm cedar sleeping carriage, every hallway sconce has been turned down to a low honey ember, casting long, velvety shadows across the smooth timber paneling and thick woven runner rug."),
    (4, "Conductor Barnaby walks with hushed, unhurried steps beside Pip the dormouse, pausing softly outside the fourth arched cedar door where a tiny brass number plate gleams in the dim amber glow."),
    (5, "Welcome to Episode Five, the calm series finale of The Slow Night Train, settling tonight into the quiet sleeping berth at Starlight Summit with zero music and only the gentle hush of the hills."),
    (6, "Barnaby turns the smooth brass door handle without a sound and pushes the paneled cedar door gently inward, revealing the coziest little sleeping compartment on the entire mountain line."),
    (7, "Warm dry cedar air greets Pip at once, carrying the faint, clean scent of sun-dried linen sheets, brushed wool, and a tiny cloth sachet of dried mountain lavender tucked beneath the pillow."),

    # Segment B (08..26): Settling Into the Patchwork Cedar Berth (02:00 - 07:00)
    (8, "Along the inner wooden wall sits a low, wide cedar berth fitted with a thick mattress of soft goose down and covered by a stitched patchwork wool quilt in muted moss, ochre, slate, and cream."),
    (1, "Beside the head of the bed stands a small carved wooden shelf holding a clear glass carafe of cool mountain water, a folded linen handkerchief, and a single tiny brass wall lamp."),
    (2, "Across from the berth, a deeply recessed arched window frames the tranquil snow-dusted pines outside, with a warm iron radiator sighing softly beneath the sill to keep the glass cozy."),
    (3, "Conductor Barnaby sets Pip's little stitched linen satchel neatly onto the wooden wall peg beside the door, making sure the leather straps hang flat and still so nothing can tap during the night."),
    (4, "Here is your quiet berth for Starlight Summit, young Pip, Barnaby whispers in a voice softer than falling snow, smoothing the cream linen sheet down along the edge of the patchwork quilt."),
    (5, "Pip opens his tiny linen satchel one last time before sleep and lifts out his two quiet travel keepsakes: his pressed cedar leaf in cream parchment and the smooth grey river pebble from the viaduct."),
    (6, "He lays the pressed cedar leaf and the silky warm river stone side by side upon the small wooden shelf beside his pillow, right where the tiny amber wall lamp paints them in soft honey light."),
    (7, "Next, Pip unwinds his knitted ochre scarf slowly from around his neck, folds it into a neat warm square, and drapes it gently over the rounded wooden footboard of the cedar berth."),
    (8, "He kicks off his small muddy boots onto the woven wool mat beside the bed, curls his velvety brown paws beneath him, and climbs effortlessly onto the plump feather mattress."),
    (1, "At once, the soft down cushions yield gently around his shoulders and knees, cradling him as warmly as a mossy hollow lined with autumn leaves deep inside an old oak tree."),
    (2, "Barnaby steps quietly closer and draws the thick patchwork wool quilt smoothly up to Pip's chin, tucking the heavy brushed edge snugly along his back so no stray evening chill can reach him."),
    (3, "In just a few quiet minutes, Old Fern will ease our wooden train into the sheltered timber shed at Starlight Summit, Barnaby murmurs kindly, where we will rest undisturbed until morning sun."),
    (4, "Will Mrs. Wren and Old Fern sleep soundly too, Pip asks in a tiny, sleepy whisper, his eyes already fluttering gently closed against the soft cream linen pillowcase."),
    (5, "Every single soul aboard the train is tucked in for the night, Barnaby answers softly, for Mrs. Wren has banked her kitchen stove, the other travelers are fast asleep, and Old Fern has his own warm cabin."),
    (6, "Barnaby reaches up with one careful paw and turns the tiny brass thumbscrew on the wall lamp down until its flame shrinks into a soft, calm amber bead barely brighter than a dying hearth ember."),
    (7, "Goodnight, young traveler, Barnaby whispers from the threshold, pulling the paneled cedar door smoothly shut behind him with one muffled, reassuring click of the brass latch."),
    (8, "Now the little sleeping compartment belongs completely to peace, warmth, and slow breathing, filled only with the soft honey shadows of the dimmed lamp and the hushed cadence of the wheels."),
    (1, "Outside the arched windowpane, the narrow iron rails curve gently into the wide, silent clearing of Starlight Summit, ringed on every side by tall snow-laden spruces standing like quiet guardians."),
    (2, "High above the dark jagged silhouettes of the alpine firs, pale silver stars gleam calmly across the deep indigo sky, steady and unhurried in the clear mountain stillness."),

    # Segment C (27..45): Resting Beneath the Pines at Starlight Summit (07:00 - 12:00)
    (3, "Up ahead in the quiet locomotive cab, Old Fern eases the brass regulator all the way home, letting the Slow Night Train glide the final twenty yards on pure, effortless momentum."),
    (4, "One slow turn of the iron wheels, then another, then a softer turn still, until the cedar carriages come to a complete, feather-light standstill beneath the sheltered timber eaves of Starlight Summit."),
    (5, "A single long, gentle sigh of warm white steam drifts lazily up from the engine chimney into the cold alpine air, curling slowly among the snow-dusted pine needles before melting into the starlight."),
    (6, "Inside the firebox, Old Fern spreads a thin, even blanket of clean grey wood ash over the glowing beechwood embers, leaving just enough quiet warmth to keep every carriage cozy until sunrise."),
    (7, "Now that the iron wheels have come completely to rest, a wonderful, deep mountain hush settles over the entire wooden train from the front locomotive cab all the way to the tidy mail car."),
    (8, "Inside Pip's sleeping compartment, the cedar walls give one last tiny, settling timber creak, and then grow utterly still and warm around the quilted berth."),
    (1, "Outside the arched windowpane, a faint alpine breeze brushes softly through the snowy pine boughs, making a low, continuous whisper like calm surf resting along a distant sandy shore."),
    (2, "Pip takes one slow, deep breath through his nose, smelling clean cedar wood, warm brushed wool, and the faint soothing trace of dried mountain lavender tucked inside his feather pillow."),
    (3, "His small paws uncurl completely beneath the heavy patchwork quilt, resting open and loose against the smooth linen sheet as every last trace of daytime tension melts smoothly away."),
    (4, "Down the corridor, the elderly hedgehog, the two young field mice, and the sketchbook barn owl all sleep deeply behind their drawn wooden doors, carried safely through the quiet hours."),
    (5, "In the dining car, the dull brass teapot sits dark and calm upon the warm iron hob, waiting patiently for tomorrow morning's clean spring water and fresh chamomile blossoms."),
    (6, "In the tidy mail car, the cedar cubbies stand empty and smooth, with Conductor Barnaby's leather ledger closed neatly beside the spool of pale flax twine on the oak sorting desk."),
    (7, "Out on the snow-dusted platform of Starlight Summit, the lone sheltered station lantern burns steadily in the clear cold air, watching quietly over the resting wooden carriages."),
    (8, "Every part of the long evening journey has been completed without a single hurried step: from the mossy rain at Pine Station, through the warm tea car, across the misty stone arches, and up the snowy ridge."),
    (1, "Now nothing moves along the mountain rails except the slow drift of starlight across the snow and the gentle rise and fall of peaceful breathing inside every warm berth."),
    (2, "Pip's breathing grows long, soft, and remarkably steady, matching the calm hush of the alpine pine wind outside the arched glass windowpane."),
    (3, "His cheek rests warmly against the plump cream pillow, his tiny ears relaxed and still, wholly wrapped in the quiet safety of the cedar compartment and the thick patchwork wool quilt."),
    (4, "There is nowhere else the Slow Night Train needs to travel until dawn paints the snow ridges pale rose and gold; tonight belongs entirely to deep, unhurried, restorative sleep."),
    (5, "Even the tiny dimmed brass lamp upon the cedar wall seems to rest more quietly now, holding its gentle amber glow steady so the shadows around the berth stay soft and comforting."),

    # Segment D (46..56): Deep Sleep Stillness & Series Finale Close (12:00 - 15:00)
    (6, "As the mountain night deepens around Starlight Summit, let your own body settle just as heavily and comfortably into your bed as Pip resting beneath his warm patchwork wool quilt."),
    (7, "Feel the smooth support of the pillow beneath your head and the gentle weight of the blanket resting across your shoulders, keeping you completely warm and safe through every hour ahead."),
    (8, "Let your jaw soften, let your hands uncurl easily at your sides, and let your breathing grow slow, deep, and effortless, moving in and out like the quiet pine breeze outside the window."),
    (1, "Every thought from today has already arrived at its own quiet station and stepped calmly down onto the platform, leaving your mind wide, clear, and peacefully empty."),
    (2, "Picture the three small cedar carriages resting still beneath the snow-dusted pines at Starlight Summit, their dimmed amber windows glowing softly under a vast, silent sky of pale stars."),
    (3, "Listen to the low, steady crackle of banked beechwood embers and the soft whisper of alpine wind moving slowly through the evergreen needles outside the frosted glass."),
    (4, "Nothing asks for your attention tonight, and nothing will interrupt this calm stillness; the rails are quiet, the timber walls are warm, and morning will arrive in its own unhurried time."),
    (5, "All five quiet stages of The Slow Night Train have carried you safely from twilight rain to starlit summit stillness, leaving only gentle breath and deep, peaceful rest."),
    (6, "Keep your eyes closed softly, let the quiet mountain air ease every remaining thought away, and sink comfortably into the deepest, calmest corner of sleep."),
    (7, "Goodnight to Pip in his quilted cedar berth, goodnight to Conductor Barnaby, Mrs. Wren, and Old Fern resting safely along the sheltered summit line."),
    (8, "And goodnight to you, resting warmly and peacefully beneath the quiet stars until morning light returns softly through the pines."),
]
