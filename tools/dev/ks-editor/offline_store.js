(function (root) {
  "use strict";

  const DB_NAME = "mo-kiss-ks-editor";
  const DB_VERSION = 1;
  const STORES = ["files", "drafts", "outbox", "meta"];

  function requestToPromise(request) {
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("IndexedDB request failed"));
    });
  }

  class OfflineStore {
    constructor() {
      this.dbPromise = null;
    }

    open() {
      if (this.dbPromise) return this.dbPromise;
      if (!("indexedDB" in root)) {
        this.dbPromise = Promise.reject(new Error("IndexedDB is not available"));
        return this.dbPromise;
      }
      this.dbPromise = new Promise((resolve, reject) => {
        const request = root.indexedDB.open(DB_NAME, DB_VERSION);
        request.onupgradeneeded = () => {
          const db = request.result;
          STORES.forEach((name) => {
            if (!db.objectStoreNames.contains(name)) db.createObjectStore(name, { keyPath: "id" });
          });
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error || new Error("IndexedDB open failed"));
      });
      return this.dbPromise;
    }

    async put(storeName, value) {
      const db = await this.open();
      const tx = db.transaction(storeName, "readwrite");
      const request = tx.objectStore(storeName).put(value);
      return new Promise((resolve, reject) => {
        request.onerror = () => reject(request.error || new Error("IndexedDB write failed"));
        tx.oncomplete = () => resolve(value);
        tx.onerror = () => reject(tx.error || new Error("IndexedDB transaction failed"));
        tx.onabort = () => reject(tx.error || new Error("IndexedDB transaction aborted"));
      });
    }

    async get(storeName, id) {
      const db = await this.open();
      return requestToPromise(db.transaction(storeName, "readonly").objectStore(storeName).get(id));
    }

    async delete(storeName, id) {
      const db = await this.open();
      const tx = db.transaction(storeName, "readwrite");
      tx.objectStore(storeName).delete(id);
      return new Promise((resolve, reject) => {
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error || new Error("IndexedDB delete failed"));
      });
    }

    async list(storeName) {
      const db = await this.open();
      return requestToPromise(db.transaction(storeName, "readonly").objectStore(storeName).getAll());
    }

    async putFile(path, data) {
      return this.put("files", { id: path, path, data, updatedAt: Date.now() });
    }

    async getFile(path) {
      return this.get("files", path);
    }

    async putDraft(path, text, baseSha = "") {
      return this.put("drafts", { id: path, path, text, baseSha, updatedAt: Date.now() });
    }

    async getDraft(path) {
      return this.get("drafts", path);
    }

    async removeDraft(path) {
      return this.delete("drafts", path);
    }

    async enqueueWrite(write) {
      if (write.action === "save" && write.path) {
        const queued = await this.listOutbox();
        const existing = queued.find((row) => row.action === "save" && row.path === write.path && row.status === "pending");
        if (existing) {
          existing.method = write.method || existing.method;
          existing.body = write.body || existing.body;
          existing.createdAt = write.createdAt || Date.now();
          existing.attempts = 0;
          existing.status = "pending";
          existing.error = "";
          return this.updateOutbox(existing);
        }
      }
      const id = write.id || `${write.action}:${write.path}:${Date.now()}:${Math.random().toString(16).slice(2)}`;
      return this.put("outbox", {
        id,
        action: write.action,
        path: write.path || "",
        method: write.method || "GET",
        body: write.body || null,
        createdAt: write.createdAt || Date.now(),
        attempts: write.attempts || 0,
        status: "pending",
        error: ""
      });
    }

    async listOutbox() {
      const rows = await this.list("outbox");
      return rows.sort((a, b) => a.createdAt - b.createdAt);
    }

    async updateOutbox(row) {
      return this.put("outbox", row);
    }

    async removeOutbox(id) {
      return this.delete("outbox", id);
    }

    async setMeta(key, value) {
      return this.put("meta", { id: key, value, updatedAt: Date.now() });
    }

    async getMeta(key) {
      const row = await this.get("meta", key);
      return row ? row.value : undefined;
    }
  }

  root.KSOfflineStore = new OfflineStore();
})(typeof globalThis !== "undefined" ? globalThis : window);
