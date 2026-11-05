PROPOSAL — not canon. A human lore author must approve and move it into docs/lore/canon/.

# KOCH-SIMULATOR: Dialogue outlines (Ink-friendly)

Format: one Ink knot per scene (`=== knot ===`), stitches for sub-beats, `*` one-shot choices, `+` sticky choices, `-> ` diverts, `VAR`s for state. Lines are **key lines only**; writers expand. Speaker tags as Ink tags (`#Arsen`). Arsen speaks little and dry.

## Global variables
```ink
VAR azamat_approach = ""        // "cool" | "isa" | "threat"
VAR ermekova_outcome = ""      // "tied" | "card_forced" | "left"
VAR stealth_score = 0          // set by game code, read for flavour lines
VAR ending = ""                // "unmasked" | "masked"
```

## Scene list
| Knot | Mission | Trigger | Mode |
|---|---|---|---|
| nurai_voicemail | M00 | Phone during packing | Phone, one-way |
| nurai_bus_call | M00 | Seated on the bus | Phone |
| kuban_checkpoint | M01 | FaceGate refusal | Face to face |
| temirov_search_order | M02 | Enter B porch | Radio |
| nurai_brewpoint | M02 | Back room | Face to face |
| nurai_garden | M03 | Companion barks + gazebo | Walk-and-talk |
| intern_203 | M04 | Optional, room 203 | Face to face |
| temirov_first_contact | M05 | After Ermekova | Radio |
| ermekova_attic | M05 | Enter F5 office | Face to face |
| piano_room | M06 | Play the old song | Monologue + phone |
| temirov_lockdown | M06 | SIGHT shutdown | PA |
| clinic_elmira / clinic_reunion | M07 | Clinic desk / room 4 | Face to face |
| aibek_archive | M07 | Archive | Face to face |
| lind_broadcast | M08 | Cutscene + during evidence | Stage speech |
| temirov_boss | M08 | Boss phases | Shouted barks |
| ending_choice | M08 | After the boss | Choice prompt |
| epilogue_unmasked / epilogue_masked | M08 | Ending | Cutscene |

---

## nurai_voicemail (M00)
```ink
=== nurai_voicemail ===
#Nurai It's me. Don't call this number back, call the one I texted.
#Nurai He didn't leave the city, Arsen. I think he never left the building.
#Nurai There's something I can't say on the phone. Brew Point, Block B. Today, before noon. Everybody's busy with the signing.
-> END
```

## nurai_bus_call (M00)
```ink
=== nurai_bus_call ===
#Nurai You're on the bus? Good. The gate's face check. You know you can't go through it with your face.
#Arsen I know.
#Nurai Then how...
* [I'll talk my way in.] #Arsen I'll talk to the guard.
* [Don't worry about it.] #Arsen Pour me a coffee. Black.
- #Nurai After the gate, go up the alley. Back door of the café. Don't come through the front.
-> END
```

## kuban_checkpoint (M01) — 3 approaches, one canon outcome
Beats: refusal buzz → Azamat steps out (tired, thermos in hand) → "Mask off, please." → player picks approach → every branch ends with Azamat insisting on the mask and reaching for the radio → spray → knife.
```ink
=== kuban_checkpoint ===
#Azamat Morning. The machine doesn't like your face. Or it can't see it. Mask off, please.
* [Play it cool: "I'm the musician for the ceremony."] -> cool
* [Ask about Isa.] -> isa
* [Threaten him: "Open the gate."] -> threat

= cool
~ azamat_approach = "cool"
#Arsen I'm playing at the signing. Twelve o'clock, Assembly Hall.
#Azamat (checks a clipboard) Nobody told me about music. They told me about delegates, press, police.
#Azamat Guitar case. Open it on the bag rest, and the mask comes off.
-> converge

= isa
~ azamat_approach = "isa"
#Arsen Three weeks ago an intern walked out of here. Isa. Nineteen. Did you see him go?
#Azamat (pause) Interns don't walk out this gate. The ones who "resign" go out the back, at night, with an escort.
#Azamat (looks closer) You were here. Two weeks ago. The brother. Son, go home. Whatever this is, go home.
-> converge

= threat
~ azamat_approach = "threat"
#Arsen Open the gate.
#Azamat (doesn't move, sighs) I've got two kids and eleven years till pension. Don't do this.
-> converge

= converge
#Azamat Mask off. Or I call it in. Last time.
#Azamat (hand goes to the radio) Post One to Control...
// Game: prompt [Pepper spray] → prompt [Knife]. No branch, no fail.
-> END
```
Payoffs: `isa` → Post Two hint (C04 marked, ending B route named); `cool` → Arsen's later line in M08 "Told you I was playing at the signing."; `threat` → no payoff, fastest.

## temirov_search_order (M02)
```ink
=== temirov_search_order ===
#Temirov Control, Temirov. Post One is down. One male, mask, long hair, guitar case. He's inside.
#Temirov Pairs. Quiet. We have guests at noon. Nobody sees a gun before I say so.
-> END
```

## nurai_brewpoint (M02)
```ink
=== nurai_brewpoint ===
#Nurai (pulls him into the storeroom) You did that? At the gate? Everybody's radio is screaming.
#Arsen Where is he?
#Nurai I don't know. But every day somebody orders tea to Clinic room 4. Three sugars. "For the boy."
#Arsen He takes three.
#Nurai And before he disappeared he said: if anything happens, tell Arsen "the old song". I thought he was being dramatic.
* [What else did he say?]
  #Nurai That he saw your face on a screen at work. He laughed. Then he stopped laughing.
* [Why help me?]
  #Nurai Because he paid for my bus card for a month when I got stiffed by this place.
- #Nurai Take my delivery card. Gets you into C and the Clinic service door. I'll take you through the garden.
-> END
```

## nurai_garden (M03)
```ink
=== nurai_garden ===
= barks
#Nurai Left. Wait. ... Now.
#Nurai They do smoke breaks behind the east gazebo, don't go that way.
= gazebo
#Nurai He sat here at lunch. He sent me this the night before.
// Plays C09 (Isa's voice note).
#Arsen "Where we play." ... The basement studio. He used to sneak down to the pianos.
#Nurai Patrol. Go. I'm behind the counter before they miss me. Call if you need eyes.
-> END
```

## intern_203 (M04, optional)
```ink
=== intern_203 ===
#Intern (frozen, hands up) Please. I just tag faces.
* [Where's Isa's stuff?]
  #Intern Security cleared his desk. They missed the bottom of the drawer. He taped stuff there.
* [Get out of here.]
  #Intern (runs)
- -> END
```

## ermekova_attic (M05)
Beats: Ermekova does not panic; she pours tea; she frames SIGHT as safety and Isa as "unstable". Reveal: Isa alive in the Clinic. Offer: the drive for the boy. Player choice decides how Arsen leaves her; the reveal is the same in all branches.
```ink
=== ermekova_attic ===
#Ermekova You must be Arsen. Your profile undersells you.
#Arsen Where is he?
#Ermekova Safe. He had a breakdown. We are a responsible employer, we gave him care.
#Ermekova He took something that belongs to the company. Bring it to me and you both walk out the front gate. I'll even make the turnstile smile at you.
#Arsen Where. Is. He.
#Ermekova Health Center. Block A, room 4. You'll need a level three card. (taps her lanyard)
* [Tie her up and take the card.]
  ~ ermekova_outcome = "tied"
  #Arsen You'll be fine. Somebody will find you after the signing.
* [Rip the card off her neck.]
  ~ ermekova_outcome = "card_forced"
  #Ermekova (hand to her throat) You are exactly what the profile said.
* [Take the card and walk away.]
  ~ ermekova_outcome = "left"
  #Ermekova (as he leaves, picking up the phone) Chyngyz. He's going down.
- #Ermekova The node is in the basement, if that's what the boy hid it for. The studio entrance, outside, west side. You can't miss the piano.
-> END
```
Note: in all branches Ermekova survives (she can testify in ending A).

## temirov_first_contact (M05)
```ink
=== temirov_first_contact ===
#Temirov You're on Azamat's radio. He'll live, by the way. You missed everything that matters.
#Arsen You took a nineteen-year-old.
#Temirov I recovered company property. The boy came with it.
#Temirov You fixed our speakers once. You know how loud this building gets. Walk out the gate and I don't make it loud.
* [Hang up.] -> END
* ["See you at noon."] #Temirov (silence, then static) -> END
```

## piano_room (M06)
```ink
=== piano_room ===
#Arsen (sits, plays the first bars of the old song; stops on the wrong key)
#Arsen (quiet) Still out of tune. You never fixed it.
// Game: lower panel of piano 2 opens; USB drive taped inside.
#Nurai (phone) Arsen? Whole C is on the radio. Did you find it?
#Arsen He hid it where nobody at KOCH would ever touch a thing. Under a song.
#Nurai There's a door in that basement only Security uses. C-001. Whatever they're hiding runs from there.
-> END
```

## temirov_lockdown (M06, PA)
```ink
=== temirov_lockdown ===
#Temirov (PA, whole campus) Attention all staff. This is a lockdown. Stay in your rooms. Doors will not open.
#Temirov (radio, to Arsen) You just turned off the city's eyes, musician. Now it's just people. My people.
-> END
```

## clinic_elmira (M07)
```ink
=== clinic_elmira ===
#Elmira (hands up) I'm a nurse. Just a nurse.
#Arsen Room four.
#Elmira (beat; slides a folder across) He doesn't know what day it is. They wanted him quiet until after twelve. Don't pull the line out fast.
-> END
```

## clinic_reunion (M07)
```ink
=== clinic_reunion ===
#Isa (groggy) ...Arsen? You cut your hair? No. You didn't.
#Arsen I'm taking you home.
#Isa I hid it. I didn't tell them. Two days, Arsen. I didn't tell them.
#Arsen I found it. Under the song.
#Isa (laughs, cries) You always said that piano was garbage.
-> END
```

## aibek_archive (M07)
```ink
=== aibek_archive ===
#Isa He's going on air anyway, isn't he. Lind. He'll say you're a terrorist. He'll say that's why they need SIGHT.
#Arsen Then the city should see the whole thing.
#Isa The hall's AV booth. You built it. You still know the patch?
#Arsen Nobody ever changed the password.
#Isa Go. I'm good here. Books don't shoot.
-> END
```

## lind_broadcast (M08)
Beats: (1) opening cutscene speech; (2) Arsen's evidence interrupts; (3) Lind tries to regain control; (4) final standoff.
```ink
=== lind_broadcast ===
= opening
#Lind Ministers, partners, friends. This morning, an armed man in a mask attacked one of our security officers at our gate.
#Lind He is still in this building. And that is precisely why we are here. A city that cannot see cannot protect.
= interrupted
// Screen switches to C13 (Arsen's profile), C18 (annex), Isa's dataset.
#Lind (turning) What is this? Cut it. Cut the feed!
#Lind (to delegates, smiling hard) A malicious intrusion. This is exactly the threat we...
= standoff
#Lind You want money? A job? Your brother can have a job.
#Lind The contract is bigger than me. They will sign it with someone else tomorrow.
-> ending_choice
```

## temirov_boss (M08, barks per phase)
```ink
=== temirov_boss ===
= phase1   // booth gallery assault
#Temirov Booth. Two left, one right. He's a guitar player, not a soldier.
#Temirov You came back for your last invoice?
= phase2   // house lights off; Arsen can flash stage lights
#Temirov Lights. Let's see how he does without his little stage.
#Temirov (blinded) Who gave him the board?! ... Of course. He built it.
= phase3   // Temirov alone, armor, close range; pepper spray opening
#Temirov I did twelve years in uniform so people like you could play songs on the street.
#Temirov (sprayed) Sss... cheap. Like the gate.
= down
#Temirov (on the floor) Azamat... tell Azamat I'm sorry about the shift.
-> END
```
(Final line is optional; cut if the author wants Temirov unrepentant.)

## ending_choice (M08)
```ink
=== ending_choice ===
// Camera red tally light on. Lind at the lectern. Delegates hiding. Evidence on the screen.
#Lind (quiet) Do it, then. Show them who you are.
* [Take off the mask.] -> unmask
* [Pull the trigger.] -> shoot

= unmask
~ ending = "unmasked"
#Arsen (lowers rifle, pulls off the mask, looks at the camera)
#Arsen My name is Arsen. My brother is Isa. He worked here for free. Look at what they did with it.
-> epilogue_unmasked

= shoot
~ ending = "masked"
// One shot. Feed cuts to the KOCH logo.
-> epilogue_masked
```

## epilogue_unmasked (default ending A)
- Police enter the hall; Arsen sets the rifle down. Cut: Arsen and Isa walk to the gate under police escort.
- FaceGate_Out (back on backup power): "IDENTIFIED: ARSEN." Turnstile opens. Nurai behind the police tape; Azamat on a stretcher by an ambulance, looks at Arsen, says nothing.
- Text cards: "The city suspended the SIGHT contract." / "Viktor Lind was charged." / "Dr. Ermekova is cooperating." / "Arsen was charged for the attack at Post One." / "Isa plays piano again."
```ink
=== epilogue_unmasked ===
#Nurai (at the tape) You owe me a coffee.
#Arsen Black.
-> END
```

## epilogue_masked (ending B)
- Arsen carries Isa out through BLD_GuardBoothNE (Post Two, as Azamat hinted if `azamat_approach == "isa"`; otherwise Nurai radios it).
- Bus interior: radio news: "...after the terrorist attack at KOCH HQ, the city has expanded the Safe City program to all districts." Arsen puts the mask back on. Bus screen: SIGHT ad.
```ink
=== epilogue_masked ===
#Isa (half asleep on his shoulder) Did it work?
#Arsen (looks at the SIGHT ad) Go to sleep.
-> END
```
