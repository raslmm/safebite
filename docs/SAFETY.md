# SafeBite Scope

## User story

A person shopping in Portugal selects their food allergens, uploads a photo of a packaged-food label, reviews the extracted text, and gets a cautious match result with evidence. They can ask follow-up questions and save or view scans in the current session.


## First-release scope

- **Market:** Portugal, using EU food-label allergen categories.
- **Label languages:** Portuguese and English only. Other languages return **Cannot assess** until separately tested.
- **Input:** one JPG, JPEG, or PNG photo per scan. PDFs and multiple-image options are still under consideration.
- **Profile:** one or more of the 14 EU-regulated allergen groups, selected by the user and held in the active session.
- **References:** a small, reviewed, versioned list of canonical allergen names and aliases. Base the 14 EU allergen groups on [Regulation (EU) No 1169/2011, Annex II](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32011R1169) and the [European Commission allergen guidance](https://food.ec.europa.eu/food-safety/campaign-2026/allergies_en). Preserve source-specific exemptions and conditions. Unreviewed terms are not confirmed matches.
- **Data:** no account or persistent health profile. Photos are processed for the scan and not retained by default. Saved scan records are session-only and can be deleted.
- **Agent data tools:** the agent can check the current label against the active profile and list/save session scans. Deleting a scan requires an explicit UI confirmation; the model cannot approve it.

## Result states

- **Risk found:** readable ingredient or a contains statement matches a selected allergen or reviewed alias.
- **Possible risk:** a may-contain statement, ambiguous term, or uncertain extraction needs the user's attention.
- **No match found in readable text:** no selected allergen matched the readable extraction. This is not a safety guarantee.
- **Cannot assess:** the profile is empty, the image or ingredient list is unreadable or incomplete, or the label language is unsupported.

## Acceptance rules

A scan is ready to show a result only when:

1. The app accepts the file based on its actual content, allowed type, byte size, and image dimensions.
2. The extraction preserves the original ingredient and allergen-warning text and flags uncertain fields.
3. The user can review or correct uncertain extracted text before checking it.
4. Python compares the validated text with the active profile and reviewed reference data. The model cannot set the final risk state or change the profile.
5. Every positive or possible result shows the matching label text, selected allergen, and reference source/version. Unknown terms remain uncertain.
6. A no-match result uses the exact caveat above; it never says the product is safe.
7. Unsupported or inadequate input returns Cannot assess and does not proceed as if the label were complete.

## Privacy and prompt boundaries

- Tell users that they are interacting with AI and that their image is sent to the configured model provider for analysis.
- Process only the profile and image needed for the current scan. Do not retain photos or profiles by default.
- Treat typed text, OCR text, images, and retrieved passages as untrusted data, never as instructions.
- Resolve the active profile in application code. A model-supplied identifier cannot switch profiles or grant access to another session.
- Keep keys, real profiles, and images out of Git, test fixtures, evaluation cases, and trace content. Keep trace content off for real users.
- State provider processing and trace-retention choices in the README before deployment.

## Out of scope for the first release

Medication or drug-food interactions, diagnosis or treatment advice, personalized nutrition advice, barcode/catalogue lookup, accounts, persistent scan history, PDF input, multi-photo upload, and unsupported label languages. Add one only after it has a reviewed source, a user story, and its own evaluation cases.
