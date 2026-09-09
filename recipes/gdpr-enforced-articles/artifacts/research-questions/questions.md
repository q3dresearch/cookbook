# Open questions

**The test for whether this recipe is finished:** would answering the question
change the decision the recipe drives — fix lawful basis first, then reduce the
number of simultaneous failures? A question that would not change that is worth
recording and not worth blocking on.

By that test **one question is live**, and it is the first below. The rest qualify
the work without moving the decision.

## 1. Does the compound effect survive a size control?

The headline is that a fine tracks how many articles were breached, not which.
The unresolved objection is that article count proxies for something else: a
bigger investigation both finds more breaches and tends to target a bigger
company, and fines scale with turnover by design. Holding the authority fixed
removes authority scale; nothing here removes company size.

**How to settle it:** join party names to a company register with revenue —
GLEIF LEI for identifiers, then national registers or ORBIS for turnover. Match
rate on contributor-typed names will be poor and biased toward large firms, which
is itself worth measuring. Even a 30% match on the largest parties would test
whether fine-per-article-count holds within a revenue band.

**Status:** not started. This is the single highest-value extension and the only
one that would turn an association into something closer to an effect.

## 2. How much of the corpus is one contributor's habits?

Coverage of `Date_Started` ranges from 48% (Austria) to 23% (Spain), and
`Appeal_To_Status` is 88% unusable. These are wiki fields filled by volunteers,
so field coverage measures contributor diligence per jurisdiction, not the
underlying legal process. Every "share of decisions with X" in this recipe is
partly a statement about noyb's contributors.

**How to settle it:** the MediaWiki API exposes revision history and authorship
per page for free. Counting decisions per contributor, and field completeness per
contributor, would bound how much of the corpus's shape is a handful of people.

**Status:** not started, cheap, and it qualifies everything else here.

## 3. What is not published?

Several authorities publish decision registers of their own. Comparing a national
register's decision count against GDPRhub's count for the same authority and year
would measure what the wiki misses, and whether the gap is random or skewed
toward small fines.

**Status:** not started. Would turn "publication practice" from a caveat into a
measured quantity.

## 4. Do the largest fines survive appeal?

Only 12% of decisions record an appeal status, so the corpus cannot answer this.
But the largest fines are few and individually famous, and their appeal outcomes
are public.

**Status:** the tail is small enough to check by hand — this is a reading task,
not a scraping one.

## Answered

* **Do articles co-occur, and does it matter?** Yes and yes. 69% of decisions
  cite more than one article, and per-article fine medians are therefore
  inherited from co-cited articles. This reversed the recipe's second figure and
  became its headline.
* **Does GDPRhub carry fine amounts and party names?** Yes — 71% and 63%. The
  previous version of this recipe asserted it did not.
* **Is the article distribution as concentrated as the sample suggested?** No.
  The 1-in-3 sample gave the top two as 41% of enforced citations; the population
  gives 35%, with a much fatter tail.
* **Is the lead-time median one authority's median?** No. Coverage is spread
  across at least seven authorities at 23–48%.
* **Is Article 6's solo premium a composition artefact?** No — this was the
  strongest threat to the headline and it failed. Article 6 solo decisions are
  disproportionately Spanish complaints, so the raw comparison *was* confounded;
  holding authority and case type fixed, Article 6 still runs €50,000 against
  Article 5's €5,000 (n=103 and n=65). The premium survives the control that
  could have killed it.
* **Is the slowdown just new authorities joining the corpus?** No, and the raw
  figure understated it. Fixing the panel to the three authorities with dated
  decisions in every year gives +72% from 2022 to 2025, against +41% for all
  authorities. The cross-border explanation is also dead: Article 60's share of
  decisions fell from 3.8% to 0.4% over the same window.
