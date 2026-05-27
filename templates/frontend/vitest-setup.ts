/**
 * Vitest test setup file.
 *
 * Configure in vitest.config.ts:
 *   test: { setupFiles: ['./src/testing/setup.ts'] }
 *
 * MSW intercepts at the network level — same handlers work in
 * Vitest, Storybook, and development server.
 */

import "@testing-library/jest-dom/vitest";

// TODO: Import your MSW server
// import { server } from "./mocks/server";
//
// beforeAll(() => server.listen());
// afterEach(() => server.resetHandlers());
// afterAll(() => server.close());
