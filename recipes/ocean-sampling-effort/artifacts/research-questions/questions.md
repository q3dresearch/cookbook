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

---

## Answered — conservation status (part V)

**Are threatened marine species under-monitored?** *(answered — the reverse)* Against
non-threatened species from the same families matched on log10(record count), threatened
species are **better** monitored in every stratum: 31.4% vs 38.4% unseen since 2016. Concern
follows attention. Record count swings the outcome seventy-fold; threat status by a fifth.

**Can a Red List listing be reconstructed from occurrence data?** *(answered — no)* Four of five
criteria are abundance. The one spatial criterion is ruled out for **81% of CR**, and the 48 it
cannot rule out hold a median of **one record**.

**Can commercial exploitation or aquaculture be detected?** *(answered — fishing yes, farming
no)* Wild-capture species sit **+1.04 sd** above the records-vs-datasets fit (p = 0.0001);
farmed species are indistinguishable from background (p = 0.36).

**Which species enter and leave threatened status?** *(answered, from outside OBIS)* Nine GBIF-
mirrored IUCN archives give 7,517 changes across eight states. The largest flow in is **Data
Deficient → threatened (548)** — a first assessment, not a fall.

## Answered — discovery cost (part IV)

**Is the register saturating?** *(answered — no, and the failure is the finding)* A saturating
fit under-predicts 2024 in **16 of 16** classes. Log-linear is roughly unbiased, which means no
asymptote, which converts into a price: 100 more sponge species cost ~83,000 records and 100
more seabird species ~63.5M.

**When was each class described?** *(answered)* Two golden ages, 1905–09 and 2005–09, and two
world wars at −30% and −31%. Seabird taxonomy finished before photography; bristle worms gain
11.9 species a year per thousand held.

## Died — conservation status

**"Heavily observed but never assessed."** OBIS stamps `category` only for CR/EN/VU/EX, so
`None` conflates Least Concern with never-assessed.

**"Marine species are declining 5:1."** 233 of 351 worsening marine species are hard corals and
273 landed in one release. Drop them and it is 1.7:1.

**"Capture the current state and ask again in a year."** The history was already published —
six years of it, one listable directory away. *"OBIS cannot answer it"* is a fact about OBIS;
*"nobody can"* is a claim about every other publisher, made without checking one.

## Open — conservation status

**Does the coral block hold up?** Needs the next IUCN release: do the same species keep moving?

**IUCN's API v4 carries per-species assessment history** and needs a token. With one, the
genuine-versus-knowledge flag may come too, which would unblock the question this recipe most
wants.
