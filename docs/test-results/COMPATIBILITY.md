# Actual browser compatibility observations

| Browser / version | Login | Navigation | Product/inventory | Sales form | Import | Dashboard/chart | Logout | Result |
|---|---|---|---|---|---|---|---|---|
| Edge154.0.4258.48 | Observed | Observed |17/3/2 observed | Observed | Observed | Real curves and tooltip; current UNASSESSED | Sign-in screen observed | Bounded PASS |
| Chrome154.0.8037.59 | Observed | Pages opened | Opened; final values unverified | Opened | Opened | Loading only; chart unverified | Not executed | PARTIAL |
| Firefox156.0.1 | Not executed | Not executed | Not executed | Not executed | Not executed | Not executed | Not executed | BLOCKED BY TOOL POLICY |


Versions come from installed executable ProductVersion properties. Chrome and Edge are installed under Program Files; Firefox is installed under Program Files/Mozilla Firefox. The full transaction workflow was separately executed in the Codex in-app Chromium browser ([11 checks](phase6-browser.json)); its engine version was not read and is not substituted for a Chrome/Edge/Firefox result.

Edge used native Windows UI after the browser connector was unavailable. The actual UI showed the product, stock17/incoming3/allocated2, sales fields, CSV preview controls, dashboard position18/UNASSESSED, historical20728 chart lines and hover value27.857142857, immutable recommendation69.571428571, and sign-in after logout. Immediate AX text after clicks could lag the screenshot; the logout result uses the observed sign-in screenshot. [Edge dashboard AX evidence](phase6-edge-dashboard.txt), [real chart screenshot](../screenshots/final/compatibility-edge-chart.jpg), [structured observations](phase6-compatibility.json). Native window was resized/maximized during navigation and later restored by the UI; no responsive/mobile guarantee follows.

Chrome initially accepted login/navigation but CDP screenshot timed out, CUA kernel timed out, and request-header policy could not load. Final chart/logout checks are unexecuted, not successful. Firefox launched; selecting its native window **stopped Computer Use because URL-policy enforcement is unsupported for that Windows browser**. Browser automation stopped at that boundary; no alternate browser-control workaround was used. No Firefox application result is asserted. These are tooling limits, not evidence of application defects.

**Pending:** complete Chrome chart/logout and Firefox checklist using a supported approved automation surface or supervised manual testing. Edge's bounded result does not establish universal cross-browser compatibility. No mobile, assistive-technology or accessibility certification was performed.
