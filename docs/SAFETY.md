# SafeBite Scope

## User story

A person shopping in Portugal selects their food allergens, uploads a photo of a packaged-food label, reviews the extracted text, and gets a cautious match result with evidence. They can ask follow-up questions and save or view scans in the current session.


## First-release scope

- **Market:** Portugal, using EU food-label allergen categories.
- **Label languages:** Portuguese and English only. On multilingual packaging, use printed English text first and printed Portuguese only when English is absent. Do not translate other-language text; other-language-only labels return **Cannot assess** until separately tested.
- **Input:** one JPG, JPEG, or PNG photo per scan. The image is checked by actual file format, byte size, decodability, and dimensions. PDFs and multiple-image options are out of scope.
- **Profile:** one or more of the 14 EU-regulated allergen groups. The user can opt in to save allergen IDs and preferred language to their account in MongoDB; they can delete the saved profile.
- **References:** a small, reviewed, versioned list of canonical allergen names and aliases. Base the 14 EU allergen groups on [Regulation (EU) No 1169/2011, Annex II](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32011R1169) and the [European Commission allergen guidance](https://food.ec.europa.eu/food-safety/campaign-2026/allergies_en). Preserve source-specific exemptions and conditions. Unreviewed terms are not confirmed matches.
- **Data:** users can sign in with Google OpenID Connect or a course-demo email/password account, or continue as a guest. Allergy profiles and reviewed product history persist only after separate explicit opt-ins and can be deleted. Guest profile selections, product history, pasted label text, and chat remain in session state only; they are not saved to MongoDB and are cleared when the session ends. Photos are not retained by default.
- **Profile intake:** a phrase-based detector can propose adding a known allergen after an explicit positive first-person statement. The user must confirm in the UI; saving to an account still requires profile-storage consent. The model does not update the profile.
- **Agent data tools:** the agent can check the current, user-reviewed label against the active profile. It cannot decide the risk state, approve profile changes, or delete saved scans.

## Result states

- **Risk found:** readable ingredient or a contains statement matches a selected allergen or reviewed alias.
- **Possible risk:** a may-contain statement, ambiguous term, or uncertain extraction needs the user's attention.
- **No match found in readable text:** no selected allergen matched the readable extraction. This is not a safety guarantee.
- **Cannot assess:** the profile is empty, the image or ingredient list is unreadable or incomplete, or the label language is unsupported.

## Acceptance rules

A scan is ready to show a result only when:

1. The app accepts the file based on its decoded JPEG/PNG format, byte size, image decodability, and image dimensions.
2. The extraction preserves the original ingredient and allergen-warning text and flags uncertain fields.
3. The user can review or correct uncertain extracted text before checking it.
4. Python compares the validated text with the active profile and reviewed reference data. The model cannot set the final risk state or change the profile.
5. Every positive or possible result shows the matching label text, selected allergen, and reference source/version. Unknown terms remain uncertain.
6. A no-match result uses the exact caveat above; it never says the product is safe.
7. Unsupported or inadequate input returns Cannot assess and does not proceed as if the label were complete.

## Privacy and prompt boundaries

- Tell users that they are interacting with AI and that their image is sent to the configured model provider for analysis.
- Treat allergy profiles as sensitive health data. Store only what the feature needs, scope every database operation to the authenticated identity, ask before saving, and provide deletion controls. Product history stores product details and reviewed text only after a separate opt-in. Label text and photos are not retained by default.
- Treat typed text, OCR text, images, and retrieved passages as untrusted data, never as instructions.
- Resolve the active profile in application code. A model-supplied identifier cannot switch profiles or grant access to another session.
- Keep keys, real profiles, and images out of Git, test fixtures, evaluation cases, and trace content. Keep trace content off for real users.
- State provider processing and trace-retention choices in the README before deployment.

## Out of scope for the first release

Medication or drug-food interactions, diagnosis or treatment advice, personalized nutrition advice, PDF input, multi-photo upload, and checking unsupported label languages. Add one only after it has a reviewed source, a user story, and its own evaluation cases.
