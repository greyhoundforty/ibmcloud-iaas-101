# IBM Cloud IaaS Explorer

Seller-facing material that explains IBM Cloud IaaS as one foundation with four pillars on top:
**Classic Infrastructure**, **VPC**, **Power Virtual Server** and **OpenShift Virtualization**.
Everything uses the IBM Carbon Design System: its colors, IBM Plex type and official Carbon icons.

There are three pieces, from broadest to deepest:

| Piece | What it is | Source here | 
|---|---|---|---|
| **Slide deck** | Click-through presentation: highlight a pillar, reveal 4 lines, reset | `deck/project/` | 
| **Seller focus** | High-level seller discovery, the true 101, and the basis for the PowerPoint | `site/iaas-101-seller-focus.html` | 
| **Tech focus** | Tech overview of the cloud services in each IaaS offering | `site/iaas-101-tech-focus.html` | 

> A light-only copy of the tech-focus page also exists (https://claude.ai/artifact/Ddxw6ifhtwiasKDCVosvxi).
> The tech-focus page itself now defaults to light with a dark toggle, so the copy is redundant and can be deleted.

**Service-level edits happen on the tech-focus page.** The seller-focus page is the 101 narrative and the source for the deck. The rest of this README is mostly about the tech-focus page.

---

## Quick start

```sh
mise install            # python + node (node is only for `node --check` and `npm pack`)
mise run serve          # wraps site/*.html into build/ and serves http://localhost:8000
mise run check          # parse the script + verify every pill icon exists
mise run icon -- --search transit                     # find a Carbon icon name
mise run icon -- ibm-cloud--transit-gateway i-tgw     # copy it into the page's icon sprite
mise run scan-pills     # add new tech-page pill labels to site/pill-docs.yaml
mise run ingest-docs    # copy site/pill-docs.yaml onto every matching pill
mise run search-page    # rebuild the local docs-search worksheet
```

Why `serve` wraps the files: the pages are written for the claude.ai Artifact publisher, which adds the
`<!doctype html><html><head><body>` skeleton when it publishes. `scripts/preview.py` adds the same skeleton
locally so the browser doesn't fall back to quirks mode.

---

## Status of `site/iaas-101-tech-focus.html`

Each pillar gets the same four **layers** (rows). Each row has its own Carbon color, used for the tint, the
stripe, the number and the pill icons: **Networking = cyan, Compute = purple, Storage = teal,
Integrations = magenta**.

| Pillar | Networking | Compute | Storage | Integrations |
|---|---|---|---|---|
| VPC | ✅ | ✅ | ✅ | ✅ |
| Power Virtual Server (IBM data centers only) | ✅ | ✅ | ✅ | ✅ |
| Classic Infrastructure | ✅ | ✅ | ✅ | ✅ |
| OpenShift Virtualization | ⬜ | ⬜ | ⬜ | ⬜ ("Coming soon") |

A pillar with `lines: []` shows a "Coming soon" tag and can't be opened. It becomes clickable as soon as
it has one line.

---

## How `site/iaas-101-tech-focus.html` is built

Everything lives in one file, `site/iaas-101-tech-focus.html`, in three parts:

1. **`<style>`**: Carbon color tokens and layout. Light mode = Carbon *White* theme on `:root`; dark mode
   = Carbon *Gray 100* under `:root[data-mode="dark"]`. Row colors use Carbon's 10/20/60 shades in light
   mode and 100/80/40 in dark (`--cyan-bg`, `--cyan-edge`, `--cyan-ink`, …).
2. **The icon sprite**: a hidden `<svg>` with one `<symbol id="i-…">` per icon, copied from the official
   `@carbon/icons` package. Nothing loads from the network except Google Fonts (IBM Plex).
3. **`<script>`**: the content (`PILLARS`) plus the rendering code. **Most edits only touch `PILLARS`.**

### The content model

```js
const PILLARS = [
  {
    id: "vpc", icon: "i-vpc", eyebrow: "IBM Cloud VPC", title: "Virtual Private Cloud",
    lines: [                         // one entry per layer row, in order
      {
        title: "Networking",
        note: "Optional subtitle next to the row title",
        items: [                     // the cards in the row; aim for 4 so spacing stays even
          {
            name: "Private connectivity",              // card title (required)
            desc: "One or two sentences.",             // optional description
            pills: [                                   // optional service pills
              { label: "Transit Gateway", icon: "i-tgw", title: "Hover text", docs: "" },
              { label: "Cloud Connections", icon: "i-cloud-conn", badge: "Legacy", docs: "" },
              { label: "Hyper Protect Crypto Services", icon: "i-hpcs", deprecated: true, docs: "" },
              { label: "To be added", placeholder: true, docs: "" },
            ],
            // subs: ["Child item"],   // older arrow-tag style; still supported
          },
        ],
      },
    ],
  },
];
```

| Field | Effect |
|---|---|
| `pills[].icon` | Symbol id from the sprite. `mise run check` fails if it doesn't exist. |
| `pills[].title` | Hover text. Use it for detail that would crowd the card (specs, numbers, caveats). |
| `pills[].badge` | Small uppercase tag after the label ("Legacy", "Select DCs"). |
| `pills[].deprecated` | Dashed, muted pill + "Deprecated" tag. Keep these **last** in the list. |
| `pills[].placeholder` | Dashed italic "to be added" pill. |
| `pills[].docs` | Docs URL from `site/pill-docs.yaml`. `mise run ingest-docs` copies one URL onto every pill with that label. `""` leaves a non-link pill. A non-empty value must be `https://` and opens in a new tab. |
| `items[].subs` | Arrow (↳) tags under a card. Replaced by `desc` + `pills` in most places; kept as comments on VPC storage. |

Row colors come from the row's position via `const TONES = ["cyan", "purple", "teal", "magenta"]`, so
keep the row order Networking → Compute → Storage → Integrations.

### Behavior worth knowing

- **Clicking a pillar** opens its rows in a full-width panel below the four pillars. A blue tab links the
  panel to the selected pillar. Click it again, click outside, or press Esc to close.
- **Below 1024px** the rows open inside the tile instead. Pillars stack 2-up, then 1-up below 600px.
- **Theme:** light by default for everyone. The toggle saves each viewer's choice in `localStorage`. The key
  is still `iaas102-mode` after the file rename, so a saved theme is not reset.
- **Direct links:** `#vpc`, `#powervs`, `#classic` open that pillar on load.

---

## Adding the next layer (the routine)

This is the loop used for every row so far:

1. **Gather the facts** from IBM Cloud docs (or the PowerVS product-guide PDF). Note version-sensitive
   items: deprecations, end-of-life dates, data-center limits.
2. **Pick 3–4 cards** for the row (4 keeps the grid even). Write a 1–2 sentence `desc` per card in the
   seller's words, not the API's.
3. **List the pills** for each card. Look up a Carbon icon per pill:
   `mise run icon -- --search <term>`. Prefer an exact IBM Cloud icon (`ibm-cloud--…`). If none exists,
   pick a sensible generic one and note the stand-in in a comment. Never use third-party logos.
4. **Add icons** that aren't in the sprite yet: `mise run icon -- <carbon-name> <i-id>`. Reuse existing
   ids where the service is the same (e.g. `i-tgw`, `i-dl`, `i-sg`, `i-kp`) so icons stay consistent
   across pillars.
5. **Add the row** to the pillar's `lines` in `PILLARS`, in the standard order.
6. `mise run scan-pills` to add any new labels to `site/pill-docs.yaml`. Existing docs URLs stay.
   Fill the new `docs` values, then `mise run ingest-docs` to copy them onto the pills.
7. `mise run check`, then `mise run serve` and click through in light and dark at a narrow width.
8. **Publish** (see below).

### Suggested next steps

**Classic Infrastructure** has all four layers. Integrations uses the same four cards as VPC and PowerVS
(Backup and recovery, Security and compliance, Observability, Identity and Access Management). Classic
devices are not IAM-enabled, so that card uses classic infrastructure permissions instead of resource groups.

- Consider adding VPN pills to the Private card too; only Transit Gateway and Direct Link are there today.

**OpenShift Virtualization**: all four layers. Scope it to Red Hat OpenShift on IBM Cloud (ROKS) with bare
metal workers + ODF before starting.

**Open questions noted along the way:**

- PowerVS IAM: Context-Based Restrictions left out because the PDF doesn't mention it. Add it if confirmed.
- PowerVS storage: snapshots/clones and Global Replication Service sit under Integrations → Backup and
  recovery. Decide if they belong on the Storage row instead.
- Veeam is off the catalog tiles for now (replaced by *Secure Automated Backup with Compass* on VPC).
  The PowerVS PDF still mentions Veeam for AIX; it's intentionally left out.
- Power9 is deliberately omitted (6 Aug 2026 release note: closed to new clients, end of life
  31 Dec 2027). A code comment in the PowerVS Compute row records this.

---

## Publishing changes

The live pages are claude.ai Artifacts. Publishing goes through Claude. From the project folder, ask:

> Publish `site/iaas-101-tech-focus.html` to https://claude.ai/artifact/KuPPwne87c8MMm1jjswLgq

> Publish `site/iaas-101-seller-focus.html` to https://claude.ai/artifact/CmqbzBgu175Y96nmYPFyLc

Use the same URL to keep the link (and anyone it's shared with) stable. A publish without the URL
creates a new artifact.

Publishing rules the files already follow:

- Write the page **without** `<!doctype>`, `<html>`, `<head>` or `<body>`: the publisher adds them.
- Only Google Fonts may load from outside. All CSS, JS and icons stay inline.
- `localStorage` works but is per viewer and optional. Always wrap it in `try/catch`.

**Slide deck** edits go through the Slides artifact type. Its content is `deck/project/deck.json` plus one
`deck/project/slides/<id>.html` per slide (fixed 1920×1080 canvas, inline styles only, `data-transition="magic"`
with matching element ids for the morph between slides). Ask Claude to publish changed slide files to
the deck URL above.

---

## Deploy

Vercel hosts the explorer. Git origin stays `https://origin.cursor.com/ryan-tiffany/ic-onboarding.git`.
Vercel's Git import only sees GitHub, GitLab, and Bitbucket, so a push to Origin does not deploy. Use the
Vercel CLI from this clone. `vercel` has to be on your PATH (`npm i -g vercel`, then `vercel login`). The
mise tasks call that CLI. They do not install it.

```sh
mise run vercel-link    # vercel link
mise run deploy         # preview
mise run deploy-prod    # production
```

Run them from the repo root, the directory that contains `site/`, `scripts/`, and `mise.toml`. The CLI
uploads the working tree. It does not read the git host.

`vercel.json` sets the build to `python3 scripts/preview.py` and the output to `build/`. That wrap step
turns each explorer fragment into a real HTML document. `mise run serve` is only the local preview. Do not
use it as the Vercel build command. `site/pill-docs-search.html` is a local worksheet. `scripts/preview.py`
skips it, so it is not part of the deployed site. The deck is not wrapped either.

`vercel link` writes `.vercel/` on this machine. `.vercel/`, `build/`, and `.cache/` stay out of git.

---

## Sources

- IBM Cloud docs (VPC): networking overview, block/file storage, instance storage, virtual servers,
  dedicated hosts, burstable, spot, bare metal, Activity Tracker Event Routing.
- *Power Virtual Server product guide* PDF from IBM Cloud docs (created 2026-10-01): networking,
  Power Edge Router, public connectivity via VPC, storage tiers, dedicated hosts, pricing, HA/DR,
  Key Protect, Workload Protection, release notes.
- Cobalt Iron: *Deploying Secure Automated Backup with Compass* (VPC, PowerVS and Classic support).
- Carbon Design System: color tokens (White / Gray 100) and `@carbon/icons` (Apache-2.0).
