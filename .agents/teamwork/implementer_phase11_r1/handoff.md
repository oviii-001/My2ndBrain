> [!WARNING] **Skepticism Disclaimer**
> While all 94 unit/integration tests and TypeScript strict typechecks pass with 0 errors against our mock fixtures, real runtime behavior with the live backend service remains unverified against live Postgres data or live backend edge cases.

## 1. What I changed
- `src/types/grading.ts`: Defined `MarksAggregateItem`, `MarksAggregateResponse`, `MarksAggregateStats`, `PaginationMeta` (aliased to `PaginationMetadata`), and `FetchMarksAggregateOptions`.
- `src/features/grading/api/grading.service.ts`: Implemented `gradingService.getMarksAggregate` connecting to `GET /v1/batches/{batchId}/marks` via `apiClient.get`, with query params `page`, `limit`, and `search`.
- `src/features/grading/api/use-marks-aggregate.ts`: Implemented TanStack Query hook `useMarksAggregate` providing query state, data normalization (extracting `items`, `meta`, `stats` resilient to `items`/`students`/`marks` response shape), and refetching.
- `src/features/grading/admin/components/admin-marks-sheet-tab.tsx`: Built consolidated marks sheet tab featuring:
  - Stats summary cards (Total Students, Graded, Pending)
  - Debounced search filter input (by roll or name)
  - Data table with columns: Roll, Name, Supervisor Initial, Report Review (out of 60), Final Defense (out of 20), External (out of 100), Supervisor (out of 100), and Computed Grade
  - Grade status badges and formatted numeric marks
  - Empty, loading, and error states with retry functionality
  - Server-side pagination controls (Previous/Next, page indicators)
  - Client-side CSV export trigger (`marks_sheet_batch_{batchId}.csv`)
- `src/features/batches/admin/admin-batch-details-page.tsx`: Injected `AdminMarksSheetTab` as the "Grading" tab button and content view in `AdminBatchDetailsPage`.
- `docs/PHASES.md`: Updated Phase 11 status to "Completed".
- Test Suites:
  - `src/features/grading/api/__tests__/grading.service.test.ts`: Verified endpoint path, query parameter formatting, whitespace handling, and error propagation.
  - `src/features/grading/api/__tests__/use-marks-aggregate.test.tsx`: Verified hook data mapping, fallbacks, loading, error, and enabled states.
  - `src/features/grading/admin/components/__tests__/admin-marks-sheet-tab.test.tsx`: Verified table rendering, stats, headers, data formatting, loading, error/retry, pagination, and CSV export.
  - `src/features/batches/admin/__tests__/admin-batch-details-page.test.tsx`: Verified tab button rendering and tab switching mounting `AdminMarksSheetTab` with batchId.

## 2. Why
To implement Phase 11 (Marks Aggregate & Grading) as specified in `docs/PHASES.md` and `docs/BACKEND.md` (Phase 12 backend endpoint), giving admins a master consolidated marks sheet combining Report Review, Final Defense, External marks, and Supervisor marks with computed grades.

## 3. Verification Record
- **Deep Verification (ran actual tests):**
  - Ran `npx vitest run`: 21 test files passed, 94 tests passed, 0 failures.
  - Ran `$env:CI="true"; npx tsc --noEmit`: Exited with code 0, 0 TypeScript compilation errors.
  - Ran `npm run lint`: Exited with code 0, 0 ESLint warnings or errors.
- **Shallow Verification (manual run only):** Eyeballed styling class names, badge color variations, and table column layouts against existing tabs (`AdminExternalMarksTab`, `AdminReportReviewsTab`).
- **Unverified aspects:**
  - Live HTTP requests against a running backend API server and PostgreSQL database.
  - Visual layout rendering and manual keyboard navigation in a real live web browser.

## 4. Known Issues
- `Minor Robustness Risk` — If backend marks payload structure changes property names (e.g., if backend returns custom unhandled wrapper keys rather than `items`, `students`, or `marks`), items fallback to empty array.

## 5. Untested Edge Cases & Next Step
- Reviewer should test edge cases with null/missing individual mark components (e.g. absent students, incomplete review submissions), non-integer marks with multiple decimal places, and batches with large volume (>1,000 students).
