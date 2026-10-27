import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, getToken, setToken } from "@/api/client";

describe("token storage", () => {
  afterEach(() => setToken(null));

  it("round-trips a token through localStorage", () => {
    setToken("abc123");
    expect(getToken()).toBe("abc123");
  });

  it("clears the token when set to null", () => {
    setToken("abc123");
    setToken(null);
    expect(getToken()).toBeNull();
  });
});

describe("api client", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    setToken("test-token");
  });
  afterEach(() => {
    global.fetch = originalFetch;
    setToken(null);
  });

  it("attaches the bearer token by default", async () => {
    let capturedHeaders: Headers | undefined;
    global.fetch = vi.fn(async (_url, init) => {
      capturedHeaders = new Headers(init?.headers);
      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    }) as typeof fetch;

    await api.get("/health");
    expect(capturedHeaders?.get("authorization")).toBe("Bearer test-token");
  });

  it("omits the token when auth is false", async () => {
    let capturedHeaders: Headers | undefined;
    global.fetch = vi.fn(async (_url, init) => {
      capturedHeaders = new Headers(init?.headers);
      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    }) as typeof fetch;

    await api.get("/health", { auth: false });
    expect(capturedHeaders?.has("authorization")).toBe(false);
  });

  it("throws ApiError with the server detail on a non-2xx response", async () => {
    global.fetch = vi.fn(
      async () => new Response(JSON.stringify({ detail: "nope", code: "bad" }), { status: 400 }),
    ) as typeof fetch;

    await expect(api.get("/x")).rejects.toMatchObject({
      message: "nope",
      status: 400,
      code: "bad",
    });
  });

  it("wraps a network failure in ApiError", async () => {
    global.fetch = vi.fn(async () => {
      throw new TypeError("network down");
    }) as typeof fetch;

    await expect(api.get("/x")).rejects.toBeInstanceOf(ApiError);
  });

  it("sends a JSON body on post", async () => {
    let capturedBody: string | undefined;
    global.fetch = vi.fn(async (_url, init) => {
      capturedBody = init?.body as string;
      return new Response(JSON.stringify({}), { status: 200 });
    }) as typeof fetch;

    await api.post("/chat", { message: "hi" });
    expect(JSON.parse(capturedBody ?? "{}")).toEqual({ message: "hi" });
  });
});
