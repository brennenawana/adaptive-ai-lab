# Writing Principles for the Playbook

Authoring guidance. Not a published chapter — this file is excluded from the site.

## What this is for

The playbook was written in a compressed register that assumes the reader already holds
its full vocabulary. That register is being replaced. This file states the principles the
rewrite is held to, and the tests an adversarial reviewer checks it against.

It states **principles, not model sentences.** An author handed a sample sentence imitates
its surface — you get fifteen chapters opening on the same rhythm, and the sample costs
context in every session without generalizing to content it never covered. An author
handed a principle *and the test that checks it* can apply it to anything. A reviewer
working from principles critiques what is actually on the page. A reviewer working from
samples can only measure distance from a reference, which is not the same question.

## The goal

Any reader should be able to read any sentence once, and come away asking *"how does this
apply to my project?"* — not re-reading to find where the sentence resolves.

The reader might be a staff engineer at a bank or a sixteen-year-old with a Raspberry Pi.
Both get the same text. **Clarity is not a concession to beginners.** The sentence that
lets the newcomer in costs the expert nothing; the expert just reads it faster.

What changes: sentence construction, ordering, and the assumed vocabulary.
What does not change: any claim, number, threshold, formula, or evidence label.

---

## The principles

Each is written **rule → why → test**. The test is what the review pass runs.

### 1. Plain sentence before the named term

**Rule.** Explain the idea in ordinary words, then name it.

**Why.** A term is a pointer. A pointer to something the reader does not yet hold costs
them a lookup and breaks their momentum — and most readers do not take the lookup, they
just proceed with a gap. Naming the concept *after* explaining it turns the term into a
compression the reader now owns and can use for the rest of the book. This is what demotes
the glossary from a prerequisite to a reference.

**Test.** Find the first use of each technical term in the file. Is the idea it names
already on the page in ordinary words? If not, the term is unearned.

### 2. One idea per sentence

**Rule.** Each sentence carries one claim.

**Why.** The reader holds every clause open until the sentence resolves. Three ideas in
one sentence means the first is already decaying while the third arrives. The information
was transmitted; it was not received.

**Test.** Split the sentence at its conjunctions and clause boundaries. If more than one
fragment could stand as its own claim, the sentence was doing more than one job.

### 3. Concrete before abstract

**Rule.** State a situation the reader can picture, then state the rule it implies.

**Why.** An abstraction is a compression of cases. Handed the abstraction first, the reader
has nothing to compress and must take the claim on trust. Handed a case first, they build
the abstraction themselves — which is why it stays built.

**Test.** Does the passage give the reader something to picture before it gives them a
rule? If it opens on the rule, it is asking them to accept a claim they cannot yet
evaluate.

### 4. Every passage leaves the reader something to do

**Rule.** Sections and scenarios end with what this changes about the reader's own work.

**Why.** This is read mid-project, by someone with a decision in front of them. Guidance
that only pays off after adopting the whole framework pays off for almost nobody.

**Test.** If a reader stopped at the end of this section, could they act on it Monday
without reading three more chapters first?

### 5. Rigor is preserved exactly

**Rule.** Change how it reads. Never change what it claims.

**Why.** The goal is accessible language, not diluted content. Softening a claim so it
reads easier is a different edit and a worse one — it makes the playbook wrong rather than
dense. A reader who cannot act on a precise claim is a writing failure; a reader who acts
on an imprecise one is a much bigger failure.

**Test.** Diff against the source. All of the following survive unchanged, or the change
is deliberate and recorded:

- numbers, thresholds, sample sizes, effect sizes
- formulas and their variable definitions
- evidence-strength labels (`consensus`, `strong-evidence`, `inference`, …)
- hedges and scope limits — "on knowledge tasks", "for clustered domains", "measured on
  this project's data" are load-bearing, not filler
- citation IDs and what they are cited *for*
- the distinction between what is measured, what is inferred, and what is asserted

### 6. No audience-narrowing

**Rule.** Write clearly for everyone. Do not write *for* beginners.

**Why.** Writing down to an imagined novice produces toy examples, padding, and
condescension — and it drives away the expert without actually helping the newcomer.
Clear writing helps both and insults neither. Examples should span real scales; the
*sentences* are the thing that stays simple.

**Test.** Is this sentence worse for a staff engineer? "A bit simple" is the target, not
a defect. "It lost precision" is a violation of principle 5.

---

## The adversarial review pass

Every rewritten file gets reviewed before it is committed. The review is a separate pass
with no stake in the draft.

**Protocol.** For each finding, cite the specific principle, quote the failing text, and
say what the failure is. "This reads awkwardly" is not a finding. "Principle 1 — `effective
N` is used in §3 but not explained until §7" is.

**Order matters.** Run principle 5 first and mechanically — diff the numbers rather than
eyeballing them. A file that lost a threshold is broken regardless of how well it reads;
no point reviewing prose in a file that has to be redone.

**A finding is not automatically a change.** Some density is load-bearing: a formula's
statement, a precise scope limit, a legal or safety constraint. If applying a principle
would violate principle 5, principle 5 wins and the finding is recorded as declined.

**Watch for uniformity, not just drift.** The failure mode of a shared style guide is
fifteen chapters that sound identical. Chapters differ in what they have to say and should
differ in how they say it. A reviewer noting "this doesn't open the way chapter 04 does"
is enforcing the wrong thing.

---

## Calibration

One before/after pair, to fix the size of the gap. **Do not imitate its surface.** It is
here to show how far the rewrite goes, not to supply a template — the sentence shapes
below are correct for this content and are not correct for all content.

Before:

> Before believing any low score, validate the instrument: measure reachability ceilings,
> check inversions, review cross-arm disagreement. A large share of apparent model failures
> are instrument defects, and the two are initially indistinguishable.

After:

> Your model scored 34%. Before you conclude the model is bad, prove your test isn't.
>
> A striking share of "the model failed" turns out to be "the test was broken" — a question
> that was never answerable, a scorer rejecting correct answers, a file the model was
> supposed to read that wasn't there. From the outside, these look identical to real model
> weakness. You cannot tell them apart by staring at the score.
>
> So you check the instrument first. Every time:
>
> - **Can this even be passed?** Answer one question yourself, by hand, using only the
>   tools the model had. If *you* can't score full marks, no model can — and that score is
>   measuring your test, not the model. *(→ reachability ceiling)*

Note what did and did not happen. Three named checks went in, none came out. The claim
("a large share") was not strengthened or weakened. What changed is that the reader now
has a picture before they have a term, and the terms arrive as labels for things they have
already understood.
