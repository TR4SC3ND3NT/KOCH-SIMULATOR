# AI-assisted "AAA-looking" UE5 workflows and legal limits on reusing other games' characters, mechanics and assets

_Research notes, 2026-11-27. Not legal advice. **Only five pages were opened in full:** Epic's Unreal MCP doc, the StraySpark blog, the daily.dev 72-hour post, fab.com/eula and the Copyright Office games page. Everything else comes from search-result summaries: the court opinions, law-firm pages, Copyright Office AI pages, Meshy/Tripo/Mixamo pages and the X posts. Check the primary text before relying on exact wording. The Epic Content License and CG Channel pages returned HTTP 403._

## 1. What the AI workflow actually is (MCP, coding agents, AI 3D/mocap), and how much of the "AAA look" is Unreal defaults

### Takeaway
Epic's own MCP server ("Unreal MCP", plugin ID `ModelContextProtocol`) arrived in **UE 5.8 as experimental, not in 5.6**. It lets Claude Code, Cursor, Codex and others drive the editor through toolsets. In practice the agent writes logic and runs editor operations, AI 3D generators (Tripo, Hunyuan) supply props, and humans still compose scenes. The photoreal look in viral clips comes mostly from Megascans/store assets plus UE5 rendering, not from AI.

### Cited Findings
**Epic's Unreal MCP (primary doc)**
- **Names.** The display name is "Unreal MCP". The identifier in source, `.uplugin` files, C++ symbols and console commands is `ModelContextProtocol` — [Epic docs: Unreal MCP in Unreal Editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- **Version and status.** The doc page is now titled for UE 5.9. It is labelled Experimental: "Many features are still under development and APIs and data formats may change at any time." — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- **When it shipped.** The plugin first shipped with UE 5.8 around State of Unreal 2026 as an "experimental, first-party MCP server". The tool set is deliberately minimal, each tool call is its own undo entry, read-back tools are limited, and Epic calls MCP core infrastructure it will carry into UE6 — [StraySpark blog (vendor of a competing commercial MCP server; treat as biased)](https://www.strayspark.studio/blog/epic-official-mcp-plugin-ue5-8-vs-third-party)
- **Ship date conflict.** Secondary sources disagree: one says June 17, 2026, another June 23, 2026 — [3daistudio](https://www.3daistudio.com/3d-generator-ai-comparison-alternatives-guide/unreal-mcp); [VP Land](https://www.vp-land.com/stories/unreal-engine-5-8-embeds-an-mcp-server-so-ai-agents-can-drive-the-editor)
- **Modules.** There are three modules: `ModelContextProtocol` and `ModelContextProtocolEngine` (runtime) and `ModelContextProtocolEditor` (editor auto-start). It depends on the Toolset Registry plugin. Toolsets are written in C++ (`UToolsetDefinition`) or Python (`unreal.ToolsetDefinition`). Agent skills use `unreal.AgentSkill` — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- **Server and tool search.** The server runs at `http://127.0.0.1:8000/mcp` and auto-starts by default. Tool search is on by default and exposes 4 meta-tools (`list_toolsets`, `describe_toolsets`, `describe_tools`, `call_tool`) instead of every tool — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- **Clients.** Supported clients: Claude Code, Codex, Cursor, Gemini CLI, VS Code with Copilot, and MCP Inspector. The in-editor "Unreal Assistant" panel works with Claude Code, Codex, Cursor, OpenCode and custom ACP agents — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- **Security and limits.**
  - There is no authentication layer, only a localhost bind and an Origin allow-list.
  - Tool calls run one at a time on the game thread.
  - Transports are Streamable HTTP and SSE only (no stdio or WebSocket). There are no prompts and no MCP Resources from engine toolsets.
  - Cooked builds expose only tools marked `AIRuntimeCallable`.
  - Live Coding does not pick up new `UFUNCTION` tools.

  — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- **Claude Code plugin.** Epic also publishes a Claude Code plugin, installed with `/plugin install unreal-engine-skills-for-claude-code@claude-plugins-official` — [3daistudio (secondary)](https://www.3daistudio.com/3d-generator-ai-comparison-alternatives-guide/unreal-mcp)
- **Community servers.** Servers such as chongdashu/unreal-mcp remain relevant, especially for older engine versions. The official plugin is Unreal-only and tied to Epic's release cadence — [3daistudio](https://www.3daistudio.com/3d-generator-ai-comparison-alternatives-guide/unreal-mcp)

**What creators actually combine**
- **72-hour platformer.** "I Built My Dream Game in 72 Hours — Assets by AI, Gameplay by Claude Code" is a Banjo-Kazooie / Mario 64-style platformer in UE 5.8.
  - 3D assets were AI-generated through an "Asset Hub" using Tripo and Hunyuan models.
  - Rigging and scene assembly were done in Blender.
  - Claude Code with native MCP wrote the logic: collectibles, lever doors and bridges, health, damage zones.
  - Lights, lanterns and props were **placed by hand**, because Claude Code and Codex could not reliably do vision-based placement from screenshots. Precise prompts ("slide along the X axis") worked better than vague ones.

  — [daily.dev summary](https://daily.dev/posts/i-built-my-dream-game-in-72-hours-assets-by-ai-gameplay-by-claude-code-eedcr1c11) of [YouTube video](https://www.youtube.com/watch?v=k9cbm5jSOxk) (aggregator; creator not named)
- **Endless runner.** In another write-up, Claude Code built a playable endless runner in UE5 through two open-source MCP plugins, "Unreal Claude" and "Vibe UE". The author found the logic fine but the Blueprints messy — [daily.dev (snippet only)](https://daily.dev/posts/claude-code-took-over-unreal-engine-5-and-built-a-game-lsf8camb8)
- **Real-world look.** The "AAA" realism in the viral Unrecord bodycam footage (2023, not AI) was built from **Megascans, Unreal Marketplace assets and bespoke assets**, "handcrafted", not scanned. IGN downloaded the same UE5 level assets (compiled by BlueDrake42) used in the 2022 trailer. The developer posted editor and noclip footage to prove it was real-time — [Windows Central](https://www.windowscentral.com/gaming/pc-gaming/unrecord-the-game-that-looked-too-real-to-be-true-until-now); [PC Gamer](https://pcgamer.com/unrecord-dev-posts-noclip-video-to-prove-the-realistic-bodycam-fps-isnt-fake); [mp1st](https://mp1st.com/news/unrecord-bodycam-fps-devs-prove-gameplay-footage-is-legit-by-sharing-unreal-engine-5-editor-video)

**AI mocap from video**
- **Rokoko's own view.** Rokoko's October 2025 article on vision-AI mocap notes inconsistent accuracy and occlusion problems with monocular video — [Rokoko](https://www.rokoko.com/insights/the-future-of-motion-capture)
- **DeepMotion.** The free plan is reportedly for personal, non-commercial use only — [itechguides comparison (SEO page, unverified)](https://www.itechguides.com/compare/deepmotion-animate-3d-vs-rokoko-create/)

### Inferences
- **Our setup matches the documented pattern.** We use Claude Code with Epic's Unreal MCP and VibeUE, plus MetaHumans and Lyra/GASP assets. Agents are strong at C++/Blueprint logic and batch editor operations. Spatial set dressing, lighting and composition still need a human eye or screenshot review.
- **Where the look comes from.** In these videos it comes mainly from scanned assets (Megascans/Fab), Lumen/Nanite/VSM and careful lighting and composition. AI 3D generators produce props, not hero-quality photoreal environments.

### Gaps
- **No primary data on Lumen, Nanite and City Sample.** I found nothing that quantifies how much of the look in specific AI videos comes from these defaults versus AI. That claim is an inference.
- **VibeUE and community servers.** I did not fetch VibeUE's or chongdashu/unreal-mcp's own docs. Their feature lists and 5.8/5.9 compatibility are unverified here.
- **Other tools not researched.** No first-hand sources on Cascadeur's AI-assisted animation, MetaHuman Animator quality, Move.ai pricing and terms, Rodin or Hunyuan3D licence terms, or AI texture tools.
- **No mocap comparison.** I found no credible head-to-head test of Move.ai, Rokoko Video and DeepMotion; search results were vendor or SEO pages.

## 2. Specific viral examples, what creators disclosed, and typical exaggeration

### Takeaway
The big 2026 viral posts are self-reported X/YouTube claims. Typical disclosures name Claude, an MCP server, Tripo/Higgsfield for assets and Blender for cleanup. None I found was independently verified, and costs or hidden manual work are often mentioned only in passing.

### Cited Findings
- **Stefan 3D AI (X, ~995.5K views, Nov 24, 2026).**
  - **Claim:** an open world "from scratch in the new Unreal Engine 5.9" with five races (male and female) and 16 quests with combat, built in one week.
  - **Cost:** "$6,528 of Claude Fable 5.2 tokens", needing "5 Claude Ultra subscriptions plus a ChatGPT one on a cloud PC with 24GB VRAM".
  - **Assets:** art and sound through Higgsfield MCP, 119 3D models on Tripo, and 1000+ images.
  - No breakdown was published.

  — [X post](https://x.com/Stefan_3D_AI/status/2125143321098264592) (via search summary)
- **Pat Simmons (X, ~532.7K views).** The post says "you can now build entire video games just by talking to Claude" after the launch of Unreal's MCP server. The demo includes cloning a real city from Google Earth with Cesium and custom Blender buildings, so non-AI data and tools carry much of the visual result — [X post](https://x.com/per_simmons_/status/2069588907801424263)
- **flopperam (2025).** An early TikTok demo connects a community Unreal MCP server to Claude for automated editor actions from natural language — [TikTok](https://www.tiktok.com/@flopperam/video/7526669721769413901)
- **Unattributed Short.** "Claude Code + MCP Built This Unreal Engine 5 Level" is a similar demo; I could not confirm the creator — [YouTube Short](https://www.youtube.com/shorts/n6fZMFFtSOc)
- **72-hour platformer.** The creator emphasizes AI "as a tool", not one-prompt results. Scene composition was manual — [daily.dev](https://daily.dev/posts/i-built-my-dream-game-in-72-hours-assets-by-ai-gameplay-by-claude-code-eedcr1c11)

### Inferences
- **Common exaggeration patterns:**
  - "Built a game" usually means a vertical slice or a scripted demo shown in short clips.
  - Store, scanned or real-world data (Cesium, Megascans) gets credited as "AI".
  - Large spend or multiple subscriptions are buried in the post.
  - Manual placement and lighting fixes go unmentioned.
- **Treat view counts and timelines as marketing.**

### Gaps
- **No verification.** None of these projects was independently verified; I found no playable build or Steam page for the Stefan or Simmons projects.
- **Little tech-press coverage.** I found no 80.lv, Game Developer or The Verge piece auditing such a video.

## 3. Legal limits on reusing characters, mechanics and assets from other commercial games (US-centric)

### Takeaway
- **Mechanics.** A game's idea, its name or title, and its "methods for playing" are not protected by copyright. The text of the rules may be registrable.
- **Protected expression.** Art, models, animations, sounds, text and distinctive characters are protected. Copying a game's specific look and feel too closely can infringe even if you claim you only took mechanics (Tetris v. Xio).
- **Ripped assets.** Assets extracted from commercial games are the most common trigger for DMCA takedowns, including for free fan projects.
- **Licensed sources.** These have their own terms:
  - Fab Standard: any engine, no standalone redistribution.
  - UE-Only content: Unreal only.
  - MetaHumans: under the UE EULA, with AI-training limits.
  - Mixamo: royalty-free, but no redistribution of raw files.
- **AI output.** Pure prompt-generated output is not copyrightable in the US.

### Cited Findings
**Mechanics vs. expression**
- **Copyright Office on games.** "The idea for a game is not protected by copyright. The name or title given to the game and the methods for playing it are not protected by copyright." The Office does say the rules text and the graphic art may be registered — [US Copyright Office, Games (Form TX)](https://www.copyright.gov/register/tx-games.html) _(the page says "methods for playing", not "mechanics")_
- **Tetris Holding v. Xio Interactive (D.N.J. 2012, district court).** Xio's *Mino* was held to infringe Tetris.
  - The court rejected the defence that only unprotected rules and functions were copied, reasoning that such an exception would "swallow" protection, because nearly all expressive elements relate to rules.
  - It held that how a developer expresses the rules is protectable.
  - It granted summary judgment on trade dress as well, and denied fair use.

  — [Justia opinion, doc 61](https://docs.justia.com/cases/federal/district-courts/new-jersey/njdce/3:2009cv06115/235418/61); [Loeb & Loeb summary](https://www.loeb.com/zh-hans/insights/publications/2012/06/tetris-holding-llc-v-xio-interactive-inc); [PC Gamer](https://www.pcgamer.com/court-declares-tetris-clone-a-breach-of-copyright-big-implications-for-derivative-games/)
- **Spry Fox v. 6waves Lolapps (W.D. Wash., filed Jan 2012).**
  - Spry Fox alleged that *Yeti Town* copied *Triple Town*, including details such as the specific prices of items in the shop.
  - Commentators said Tetris made the "it's just the idea" defence harder.
  - The case **settled** in Oct 2012, with Spry Fox owning the IP for both games. There is no merits ruling.

  — filing and settlement: [Wikipedia summary](https://en.wikipedia.org/wiki/Spry_Fox,_LLC_v._Lolapps,_Inc.); the shop-prices and "harder defence" commentary came via a search summary with no clear source (likely [PC Gamer's Tetris piece](https://www.pcgamer.com/court-declares-tetris-clone-a-breach-of-copyright-big-implications-for-derivative-games/))

**Characters**
- **DC Comics v. Towle (9th Cir. 2015).** The Batmobile was held a protectable "character". The test asks whether a character is sufficiently delineated, with consistent and recognizable characteristics (three-part test derived from *Air Pirates*). Replicas infringed — [Justia (9th Cir. opinion)](https://law.justia.com/cases/federal/appellate-courts/ca9/13-55484/13-55484-2015-09-23.html); [Stanford Fair Use](https://fairuse.stanford.edu/case/dc-comics-v-towle/)
- **Stock characters.** Commentators note a low delineation threshold, but say stock or archetypal characters are less protectable. The Booker T. v. Activision commentary (*Call of Duty: Black Ops 4*) argued that a "stock character" is not distinctive enough — [Above the Law](https://abovethelaw.com/?p=1121627); [Golden Gate Univ. Law Review](https://digitalcommons.law.ggu.edu/ggulrev/vol47/iss1/6)

**Ripped assets and fan projects (news reports, not legal analysis)**
- **EA vs. OpenSC2K.** EA had the OpenSC2K SimCity 2000 remake removed from GitHub because its sprites were ripped from the original — [PC Gamer](https://www.pcgamer.com/au/ea-takes-down-open-source-simcity-2000-remake-for-using-copyrighted-assets/); [Game Developer](https://gamedeveloper.com/production/-i-simcity-2000-i-remake-removed-by-ea-for-using-copyrighted-assets)
- **Nintendo vs. DMCA Royale.** Nintendo took down *Mario Royale*, and then its reskinned version *DMCA Royale*, which still kept the same level layout — [Techdirt](https://www.techdirt.com/2019/06/28/nintendo-does-nintendo-mario-royale-fan-game-becomes-dmca-royale-is-now-dead/)
- **Nintendo on Game Jolt.** Nintendo removed hundreds of Game Jolt fan games in 2016 — [Hackaday](https://hackaday.com/2016/09/07/nintendo-wields-dmca-axe-on-fan-games)
- **Microsoft vs. a Halo mod.** A non-profit Halo mod for CS2 got a DMCA notice. Mods "inspired by" other games, rather than ripped from them, tend to survive — [Windows Central](https://www.windowscentral.com/gaming/halo/microsoft-dmca-takedown-project-misriah-halo-cs2-mod/)
- **Valve vs. a TF2 port.** Valve's takedown of a TF2 port cited assets ported to Source 2 and redistributed without permission — [GamingOnLinux](https://www.gamingonlinux.com/2024/01/team-fortress-source-2-fan-project-gets-a-dmca-from-valve/comment_id=255938)

**Fab and Epic content**
- **Fab Standard License.**
  - Allowed: commercial use, modification, distributing products that include the asset, and "Use the assets with any compatible tools (usage is not limited to Unreal Engine)".
  - Prohibited: "Resell or redistribute the asset for free on a standalone basis or allow others to do the same."
  - Credit is not required.
  - The Personal and Professional tiers grant the same rights, and there is no need to upgrade if revenue crosses the threshold after purchase.

  — [Fab EULA summary](https://www.fab.com/eula)
- **Megascans on Fab.** Under Fab Standard, Megascans can be used in any engine. Under the older Epic Content License, assets obtained through the UE plan were Unreal-only — [Epic Fab launch blog](https://www.unrealengine.com/blog/fab-epics-new-unified-content-marketplace-launches-today?lang=en-US); [Megascans update, March 2025](https://forums.unrealengine.com/t/megascans-update-march-2025/2419561)
- **"UE-Only Content"** is defined in the Epic Content License as content licensed for use only with Unreal Engine and UE-based products (e.g. Twinmotion). Example: the Fab listing *City Sample Crowds*, extracted from City Sample, is labelled "UE-Only Content - Licensed for Use Only with Unreal Engine-based Products" — [Epic Content License (snippet; page 403)](https://www.unrealengine.com/eula/content); [Fab listing](https://www.fab.com/listings/ada3c1dd-c4c3-4e63-b4c6-bfd010b96ad7)

**MetaHuman (snippets only; primary pages returned 403)**
- **June 2025 change.** With UE 5.6, when MetaHuman Creator, Mesh to MetaHuman and MetaHuman Animator moved into the engine, Epic allowed MetaHumans to be used in other engines and DCCs, including commercially, and to be sold on marketplaces. They count as "non-engine products", so Unity or Godot games owe no 5% UE royalty — [CG Channel](https://www.cgchannel.com/2025/06/you-can-now-sell-metahumans-or-use-them-in-unity-or-godot/)
- **Revenue threshold.** MetaHuman is covered by the standard UE license and is free under $1M USD in revenue — [metahuman.com/license](https://www.metahuman.com/en-US/license)
- **AI restriction.** The 2025 terms barred **training or enhancing AI models** with MetaHumans. Using them in AI-assisted workflows was allowed — [CG Channel](https://www.cgchannel.com/2025/06/you-can-now-sell-metahumans-or-use-them-in-unity-or-godot/); [UE EULA change log](https://www.unrealengine.com/eula-change-log/unreal)
- **Later opt-in.** Epic later added an **opt-in** EULA letting developers train AI models on their UE and MetaHuman projects; a localized copy is dated 29 Oct 2026 (unconfirmed). Custom-license holders are governed by their own agreements — [Epic post](https://unrealengine.com/ue-devs-can-now-choose-to-train-ai-models-on-their-projects)

**Mixamo**
- **Official FAQ.** Characters and animations are royalty-free for personal, commercial and non-profit projects, including video games — [Adobe Mixamo FAQ](https://helpx.adobe.com/en/creative-cloud/faq/mixamo-faq.html)
- **Adobe staff forum post (2022, not formal terms).**
  - Raw character and animation files must not be redistributed, as asset packs or on stores; they must be baked into the game.
  - No credit is required.
  - The content may not be used to train ML models.

  — [Adobe community](https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/td-p/13234775)

**AI-generated assets**
- **Copyright Office Part 2 (Jan 29, 2025).**
  - "Purely AI-generated material" made by entering prompts is not copyrightable under current law.
  - Using AI to assist, or including AI output inside a larger human-authored work, does not bar protection for the human contribution.
  - No new legislation is recommended.

  — [Copyright Office NewsNet](https://copyright.gov/newsnet/2025/1060.html); [Copyright Office blog](https://blogs.loc.gov/copyright/2025/02/inside-the-copyright-offices-report-copyright-and-artificial-intelligence-part-2-copyrightability/)
- **Thaler v. Perlmutter (D.C. Cir., Mar 18, 2025, unanimous).** The court affirmed the refusal to register an autonomously AI-generated image; human authorship is required — [DLA Piper](https://dlapiper.com/en-us/insights/publications/2025/03/copyrightability-of-genai-outputs-in-the-us-key-developments)
- **Meshy.** Paid plans: the user owns the output. Free plan: CC BY 4.0, so commercial use is allowed with attribution (e.g. "Model created with Meshy – CC BY 4.0 License") — [Meshy help: commercial use](https://help.meshy.ai/en/articles/9992001-can-i-use-my-generated-assets-for-commercial-projects); [Meshy help: ownership](https://help.meshy.ai/en/articles/10137554-what-is-the-ownership-of-the-generated-models)
- **Tripo, free tier.** Tripo's help page says the Terms (§5.2.1) let Tripo retain all rights to free users' outputs, so commercial use needs a paid plan — [Tripo help](https://www.tripo3d.ai/help/privacy-policy/how-to-use-tripo-models-commercially); contradicted by [Tripo blog](https://www.tripo3d.ai/blog/commercial-use-ai-3d-models), which says the free tier is CC BY 4.0 with attribution

### Inferences
- **Mechanics.** Re-implementing mechanics from other games is generally lawful: a portal gun, bullet time, cover shooting, a grappling hook, a heist planner. But avoid copying a game's specific expression:
  - character designs and silhouettes
  - names and logos
  - UI layouts and icons
  - sounds, VO and music
  - specific level layouts
  - distinctive numeric tuning sets (Spry Fox's shop prices; DMCA Royale's layouts).
- **"Characters from different games".** This is high-risk if they are recognizable versions of existing characters (name, look, costume, catchphrase), even when remodelled. It is low-risk if they are new characters built from genre archetypes, such as "heavy gunner" or "agile flanker".
- **Ripped models, animations and sounds.** These are not usable: they are the owner's copyrighted works, and extracting them typically also breaches the game's EULA. Takedowns hit even free projects.
- **Our project.** We are a UE 5.8 project, so the UE-Only label on any Epic sample content (City Sample; possibly Lyra/GASP) does not restrict us, as long as we don't redistribute the raw assets or port them to another engine. MetaHumans and Mixamo can ship baked into the game. Using Claude/MCP to *drive* MetaHumans appears to be an AI-assisted workflow rather than AI training, but check the current EULA text.
- **AI-generated assets.** Our human-made arrangement, code and edits are protectable; the raw AI meshes likely are not. Free-tier Meshy assets need attribution; free-tier Tripo assets may not be commercially usable at all.

### Gaps
- **Trademarks.** I found no source on trademark rules for game names, logos and brands, or on trade dress beyond the Tetris ruling.
- **Character case law.** I found no game-specific case law on character copyright beyond the Booker T. commentary.
- **Epic sample licences.** I could not confirm whether Lyra and the Game Animation Sample carry a UE-Only label; the Epic Content License page returned 403.
- **MetaHuman terms.** The full current MetaHuman EULA text was not read.
- **Mixamo terms.** I did not check Mixamo's formal Terms of Use, only the FAQ and a 2022 staff post.
- **Other AI tools.** Rodin, Hunyuan3D, Move.ai and Rokoko Video output terms were not researched.
- **Ripped-asset legal analysis.** I found no lawyer-written explainer; there are news reports of takedowns only.
- **Non-US law.** EU and other jurisdictions were not covered.

## 4. Legal ways to get a similar "characters from different games" feel

### Takeaway
Build original characters from archetypes, re-implement mechanics in our own code with our own art, audio and names, and fill the asset gaps with properly licensed packs: Fab Standard or UE-Only, Megascans, MetaHumans, Mixamo, and paid-tier AI generators.

### Cited Findings
- **Mechanics and expression.** The idea and the "methods for playing" are unprotected, while the rules text and graphic art may be registered — [US Copyright Office](https://www.copyright.gov/register/tx-games.html). The line is drawn at specific expression — [Tetris v. Xio opinion](https://docs.justia.com/cases/federal/district-courts/new-jersey/njdce/3:2009cv06115/235418/61)
- **"Inspired by" survives better than "ripped from".** Mods inspired by other games, rather than ripped from them, can survive — [Windows Central](https://www.windowscentral.com/gaming/halo/microsoft-dmca-takedown-project-misriah-halo-cs2-mod/)
- **Stock characters.** Stock or archetypal characters are arguably less protectable than distinctive, delineated ones (commentary) — [Above the Law](https://abovethelaw.com/?p=1121627)
- **Licensed asset sources:**
  - Fab Standard (any engine) — [Fab](https://www.fab.com/eula)
  - MetaHumans under the UE EULA — [metahuman.com](https://www.metahuman.com/en-US/license)
  - Mixamo, royalty-free — [Adobe](https://helpx.adobe.com/en/creative-cloud/faq/mixamo-faq.html)
  - Meshy paid output owned by the user — [Meshy](https://help.meshy.ai/en/articles/10137554-what-is-the-ownership-of-the-generated-models)

### Inferences
- **Per enemy role:** give each role a mechanic set (e.g. a "Donk" peeker or a Heavy LMG), then an original look:
  - a MetaHuman base
  - KOCH-branded gear
  - a silhouette not traceable to a specific existing game character.
- **Paper trail:** keep a licence log per asset (source, licence, tier, date), especially for AI-tier assets.

### Gaps
- I found no source on "clearance" practice, such as how studios document originality reviews for archetype characters.
