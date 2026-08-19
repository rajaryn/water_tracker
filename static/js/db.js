/**
 * IndexedDB Local Persistence Engine
 * Supports zero-latency offline logging and optimistic UI updates.
 */

const DB_NAME = 'HydrationTrackerDB';
const DB_VERSION = 1;

let dbInstance = null;

export async function initDB() {
  if (dbInstance) return dbInstance;

  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      if (!db.objectStoreNames.contains('profile')) {
        db.createObjectStore('profile', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('bottle')) {
        db.createObjectStore('bottle', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('hydration_target')) {
        db.createObjectStore('hydration_target', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('drink_events')) {
        const drinkStore = db.createObjectStore('drink_events', { keyPath: 'id' });
        drinkStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
      if (!db.objectStoreNames.contains('refill_events')) {
        const refillStore = db.createObjectStore('refill_events', { keyPath: 'id' });
        refillStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
      if (!db.objectStoreNames.contains('sync_queue')) {
        db.createObjectStore('sync_queue', { keyPath: 'id' });
      }
    };

    request.onsuccess = (event) => {
      dbInstance = event.target.result;
      resolve(dbInstance);
    };

    request.onerror = (event) => {
      console.error('[IndexedDB] Initialization error:', event.target.error);
      reject(event.target.error);
    };
  });
}

export async function getLocalData(storeName, key) {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    const request = key ? store.get(key) : store.getAll();

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function saveLocalData(storeName, data) {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    const request = store.put(data);

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function deleteLocalData(storeName, key) {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    const request = store.delete(key);

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function addToSyncQueue(item) {
  return saveLocalData('sync_queue', {
    id: item.id || 'queue_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7),
    ...item,
    queued_at: new Date().toISOString()
  });
}

export async function getSyncQueue() {
  return getLocalData('sync_queue');
}

export async function clearSyncQueue() {
  const items = await getSyncQueue();
  for (const item of items) {
    await deleteLocalData('sync_queue', item.id);
  }
}
