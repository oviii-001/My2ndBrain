# Adversarial Review Handoff - Round 1 (Phase 10: Email - Admin Only)

## Overview
This document records the adversarial review and bug-fixing pass performed on Phase 10 ("Email - Admin Only") of the PTMS faculty portal frontend (`defense-frontend`).

## 1. What the Prior Attempt Got Wrong

### Issue 1: Fatal UI Crash on Missing/Empty Recipients in Delivery Response
- **Input:** Triggering any email action where backend response has `recipients: undefined` or `recipients: null` (legal per OpenAPI schema `recipients?: Array<string> | null`).
- **Expected:** Safe fallback rendering count (e.g. `0 recipients` or empty list without unhandled runtime exceptions).
- **Actual:** `TypeError: Cannot read properties of undefined (reading 'length')` when rendering `lastResult.response.recipients.length` in the UI summary alert.
- **Root Cause:** Direct un-bracketed property access `lastResult.response.recipients.length` in `src/features/email/admin/components/admin-email-tab.tsx` without optional chaining or nullish coalescing.

### Issue 2: Double-Dispatch Race Condition on Action Confirmation
- **Input:** Rapidly clicking "Confirm & Send" or hitting Enter key multiple times before React Query sets `isPending` state.
- **Expected:** Idempotent submission guard: duplicate clicks or key events while submission is initiated/pending must be completely ignored.
- **Actual:** Multiple concurrent HTTP POST requests dispatched to `/api/v1/emails/*`, leading to duplicate mass emails sent to faculty/supervisors.
- **Root Cause:** `handleConfirmSend` lacked an early return check `if (isAnySending) return;` at the beginning of the handler.

### Issue 3: Premature Modal Dismissal During In-Flight Mutation
- **Input:** User presses Escape or clicks modal backdrop while an email batch request is in-flight (`isAnySending === true`).
- **Expected:** Modal remains locked until the asynchronous dispatch finishes, preventing state desynchronization or accidental double-triggering.
- **Actual:** Dialog closed immediately, leaving the user without confirmation feedback while requests were still executing.
- **Root Cause:** `<Dialog onOpenChange={(open) => { if (!open) setPendingAction(null); }}>` did not check `!isAnySending` before allowing closure.

### Issue 4: Misleading Filter Labeling in Confirmation Dialog Scope
- **Input:** Selecting a specific supervisor/faculty filter ID when `facultyMembers` cache is still loading or resolving.
- **Expected:** Dialog indicates that a specific faculty ID filter is applied (`"Selected faculty: <id>"`).
- **Actual:** Displayed `"All supervisors in this batch"` or `"All faculty in this batch"`, giving the false impression that no filter was selected.
- **Root Cause:** Fallback logic evaluated `faculty?.fullName ? ... : 'All...'` instead of checking if `facultyId` was truthy.

### Issue 5: Prohibited `console.error` Violation
- **Input:** Any API failure when sending emails.
- **Expected:** Errors logged via domain error boundaries / toast notifications without leaking unformatted logs to console in production code paths (`AGENT.md` rule §3.2, §6.2).
- **Actual:** Raw `console.error('Failed to send email:', err)` was executed.
- **Root Cause:** Leftover debug statement in `handleConfirmSend` catch block.

### Issue 6: UI Feedback Gap During Faculty Dropdown Loading
- **Input:** Opening the email tab while `useFacultyMembers` query is fetching.
- **Expected:** Select placeholder explicitly informs the user that faculty options are loading.
- **Actual:** Displayed empty/static "All Faculty" option without loading indicator.
- **Root Cause:** Missing `isLoadingFaculty` indicator in SelectTrigger and option states.

---

## 2. Changes Implemented

1. **`src/features/email/admin/components/admin-email-tab.tsx`**:
   - Added early guard `if (!pendingAction || isAnySending) return;` in `handleConfirmSend`.
   - Prevented modal dismissal during active mutations via `onOpenChange={(open) => { if (!open && !isAnySending) setPendingAction(null); }}` and disabling Cancel button during dispatch.
   - Fixed scope text rendering in confirmation dialog to handle both resolved faculty names and raw IDs when filter is active.
   - Replaced unsafe `lastResult.response.recipients.length` with `(lastResult.response.recipients ?? []).length` and safe mapping.
   - Removed `console.error`.
   - Added `Loading faculty...` placeholder in filter selects when `isLoadingFaculty` is true.

2. **`src/features/email/admin/components/__tests__/admin-email-tab.test.tsx`**:
   - Added test for mid-defense schedule email dispatch.
   - Added test for final defense schedule email dispatch.
   - Added test for supervisor feedback reminder with specific supervisor filter.
   - Added test verifying safe rendering when response has empty or undefined `recipients`.
   - Added test asserting loading dropdown feedback when faculty list is loading.

3. **`src/features/email/api/__tests__/use-email.test.tsx`**:
   - Added error handling tests for all 5 mutation hooks (`useSendDefenseCallEmail`, `useSendMidDefenseScheduleEmail`, `useSendFinalDefenseScheduleEmail`, `useSendSupervisorFeedbackEmail`, `useSendAbsentSupervisorEmail`).

---

## 3. Verification Summary
- `vitest run src/features/email`: 3 files, 31 tests passed.
- `vitest run`: 17 test suites, 67 tests passed.
- `tsc --noEmit`: 0 errors.
- `eslint`: 0 errors, 0 warnings.
- End-to-end integration with `AdminBatchDetailsPage` confirmed.
- `docs/PHASES.md` updated with Phase 10 marked "Completed".
