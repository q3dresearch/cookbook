# Asked, answered, died, open

Written for a return visit. Status on every line, and the reason, so a second pass resumes
rather than restarts.

## Answered

**Is a hotspot a rich sea or a long survey?** *(answered)* A survey, usually one. Sampling 110
cells across the record-count distribution: the median cell takes 45% of its records from a
single dataset, 46% of cells are majority-one, 13% are over 90%. Worst where thinnest — in
cells of 100–1,000 records the median top dataset is 67%.

**Do taxonomic classes differ, or only their sampling?** *(answered, both)* For animals mostly
the classes. For plants, algae and single cells, the gear: rho **+0.97** between a class's
DNA-sequencing share and the share of its records below 50 m. Forams break it at 2.2%
sequencing and 39.6% below 50 m, because they arrive by sediment drill core — a third
instrument, which confirms the mechanism rather than denting it.

**Is there any cliff in this data that is biology?** *(answered — one)* Light. Benthic
photosynthesisers cross a tenth of their shallow share at 20 m (seagrass), 30 m (kelp), 50 m
(red algae), 70 m (green algae); nothing that does not photosynthesise moves at all. Stony
corals were included as a designed intermediate and behaved like one.

**Should the flagged records be excluded first?** *(answered — no)* The flags are a habitat
map: ON_LAND is 52.7% of seabirds and 31.7% of seagrasses; DEPTH_EXCEEDS_BATH picks the
opposite set, sea urchins 10.1% and kelp 9.7%. Excluding them changes none of the seven cliff
crossings and moves the top-200 m share from 88.0% to 87.6%.

## Died, with the reason

**"Map invasion pressure."** WRiMS marks a **species** if it is introduced anywhere, and the
filter then marks every one of its records including its native range. Arctic char is native to
Greenland and 325,549 of its 325,563 records are flagged. Every species sits at exactly 0% or
exactly 100%; nothing lands between.

**"Biomass density by latitude and longitude."** `organismQuantityType` is free text: 44
distinct strings reducing to 8 genuinely different kinds of measurement — counts, densities on
area *and* on volume, masses, an ordinal letter scale, sequencing reads, and one morphometric
measurement filed where a count belongs. Incommensurable by construction, not by untidiness.

**"The carbonate compensation depth should show in calcifiers."** *(blocked, not negative)*
Forams fall from 2.04% of the 3–4 km band to 0.39% of the 4–5 km band — right size, right
place. Unclaimable: sea cucumbers are 26.7% of that band on their own, and below 5,000 m one
cruise holds 46.6%.

**"Bathymetry and shore distance can be filtered on."** They cannot. Those parameters return
the unfiltered total, and so does a nonsense one.

## Open

**Can effort be reconstructed from what is there?** `sampleSizeValue`, `sampleSizeUnit` and
`samplingProtocol` exist on roughly a quarter to a third of records and have not been examined.
If effort is recoverable then absence becomes measurable, and the question this recipe circles
— is this the ocean or the fleet — becomes answerable rather than merely arguable.
Species-per-effort is blocked behind it, and so is any honest gap map.

**Has coverage improved or only grown?** Needs the grid by year. The API supports it; it has
not been pulled.

**How far does the date rot go?** Partly answered: the spatial and depth flags are a habitat
map, not an error signature, and only 25 records of 218 million predate 1750. The date half is
open — how many records carry a date before their own species was described, or a depth greater
than the sea beneath them, with the flag agreeing?

**Does a species' first record reach far enough back to be a baseline?** A 754-species probe
found 49% with no record before 1950 and 28% none before 1980, which would make IUCN's
criterion A — decline over ten years or three generations — uncheckable here for long-lived
groups. Measured but not drawn: it refines a conclusion the workspace recipe already reached by
another route, and the data is cached.
