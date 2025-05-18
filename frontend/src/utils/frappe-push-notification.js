import { initializeApp, getApp, deleteApp } from "firebase/app";
import {
	getMessaging,
	getToken,
	isSupported,
	deleteToken,
	onMessage as onFCMMessage,
} from "firebase/messaging";

// Unique name for the Firebase app instance in this PWA
const FIREBASE_APP_NAME = "education-pwa-firebase-app";

export default class FrappePushNotification {
	// Use a hardcoded server URL instead of relying on window.frappe.boot
	static get relayServerBaseURL() {
		// Use a default URL for your Frappe backend if window.frappe is not available
		// This should point to the Frappe server where education and notification_relay apps are installed
		return window.frappe?.boot?.push_relay_server_url || "http://localhost:8000";
	}

	// Type definitions
	/**
	 * Web Config
	 * FCM web config to initialize firebase app
	 *
	 * @typedef {object} webConfigType
	 * @property {string} projectId
	 * @property {string} appId
	 * @property {string} apiKey
	 * @property {string} authDomain
	 * @property {string} messagingSenderId
	 */

	/**
	 * Constructor
	 *
	 * @param {string} projectName
	 */
	constructor(projectName) {
		// client info
		this.projectName = projectName;
		/** @type {webConfigType | null}  */
		this.webConfig = null;
		this.vapidPublicKey = "";
		this.token = null;

		// state
		this.initialized = false;
		this.messaging = null;
		/** @type {ServiceWorkerRegistration | null} */
		this.serviceWorkerRegistration = null;

		// event handlers
		this.onMessageHandler = null;
	}

	/**
	 * Initialize notification service client
	 *
	 * @param {ServiceWorkerRegistration} serviceWorkerRegistration - Service worker registration object
	 * @returns {Promise<void>}
	 */
	async initialize(serviceWorkerRegistration) {
		if (this.initialized) {
			return;
		}
		this.serviceWorkerRegistration = serviceWorkerRegistration;
		
		const configData = await this.fetchWebConfig();
		
		if (!configData || !configData.config || Object.keys(configData.config).length === 0) {
			console.error("[FrappePushNotification] Initialization failed: Firebase config is missing or empty from API.");
			// Try to use fallback if API fails or returns incomplete data
			this.webConfig = {
				apiKey: "AIzaSyDummyKeyF1rebase123456",
				authDomain: "education-portal-placeholder.firebaseapp.com",
				projectId: "education-portal-placeholder",
				storageBucket: "education-portal-placeholder.appspot.com",
				messagingSenderId: "123456789012",
				appId: "1:123456789012:web:a1b2c3d4e5f6a7b8c9d0e1"
			};
			this.vapidPublicKey = "YOUR_FALLBACK_VAPID_KEY_IF_NEEDED"; // Replace if you have one
			console.warn("[FrappePushNotification] Using hardcoded fallback Firebase config.");
		} else {
			this.webConfig = configData.config;
			this.vapidPublicKey = configData.vapid_public_key;
		}
		
		try {
			let firebaseApp;
			try {
				firebaseApp = getApp(FIREBASE_APP_NAME);
				console.log(`[FrappePushNotification] Reusing existing Firebase app: ${FIREBASE_APP_NAME}`);
			} catch (e) {
				// No app exists, initialize a new one
				console.log(`[FrappePushNotification] Initializing new Firebase app: ${FIREBASE_APP_NAME}`);
				firebaseApp = initializeApp(this.webConfig, FIREBASE_APP_NAME);
			}
			this.messaging = getMessaging(firebaseApp);
			this.onMessage(this.onMessageHandler);
			this.initialized = true;
			console.log("[FrappePushNotification] Successfully initialized Firebase messaging client.");
		} catch (error) {
			console.error("[FrappePushNotification] Error initializing Firebase:", error);
			// Attempt to delete the potentially corrupt app instance to allow re-initialization on next try
			try { await deleteApp(getApp(FIREBASE_APP_NAME)); } catch (e) { /* ignore */ }
			throw error; // Re-throw to be caught by main.js
		}
	}

	/**
	 * This method might not be needed if vite-plugin-pwa handles SW registration with params
	 * or if SW fetches config directly.
	 * @param {string} url - Service worker URL
	 * @param {string} parameter_name - Parameter name to add config
	 * @returns {Promise<string>} - Service worker URL with config
	 */
	async appendFirebaseConfigToSWUrl(url, parameter_name = "firebaseConfig") {
		let config = await this.fetchWebConfig();
		if (!config || Object.keys(config).length === 0) {
			console.error("[FrappePushNotification] Cannot append Firebase config: Config is missing or empty.");
			return url; // Return original URL if no config
		}
		const encode_config = encodeURIComponent(JSON.stringify(config));
		return `${url}?${parameter_name}=${encode_config}`;
	}

	/**
	 * Fetch web config of the project
	 *
	 * @returns {Promise<webConfigType | null>}
	 */
	async fetchWebConfig() {
		if (this.webConfig && this.vapidPublicKey) { 
			return { config: this.webConfig, vapid_public_key: this.vapidPublicKey };
		}
		try {
			const apiUrl = `${FrappePushNotification.relayServerBaseURL}/api/method/education.api.get_firebase_config`;
			console.log("[FrappePushNotification] Attempting to fetch Firebase config from:", apiUrl);
			
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), 7000); // 7 second timeout
			
			let response = await fetch(apiUrl, { signal: controller.signal });
			clearTimeout(timeoutId);
			
			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`Failed to fetch Firebase config: ${response.status} ${response.statusText}. Response: ${errorText}`);
			}
			
			let response_json = await response.json();
			// The API directly returns the structure { "config": {}, "vapid_public_key": "" } or {"error": "..."}
			if (response_json.error) {
				console.error("[FrappePushNotification] Error from get_firebase_config API:", response_json.error);
				return null;
			}
			if (!response_json.config || !response_json.vapid_public_key) {
				console.error("[FrappePushNotification] Fetched Firebase config from API is incomplete.", response_json);
				return null;
			}
			
			this.webConfig = response_json.config;
			this.vapidPublicKey = response_json.vapid_public_key;
			console.log("[FrappePushNotification] Successfully fetched Firebase config from API.");
			return { config: this.webConfig, vapid_public_key: this.vapidPublicKey };
		} catch (e) {
			console.error("[FrappePushNotification] Error fetching web config from API:", e);
			return null; 
		}
	}

	/**
	 * Fetch VAPID public key
	 *
	 * @returns {Promise<string | null>}
	 */
	async fetchVapidPublicKey() {
		if (this.vapidPublicKey) { // Check if already fetched (e.g. by fetchWebConfig)
			return this.vapidPublicKey;
		}
		// Ensure webConfig (which also fetches VAPID key) is called if not already
		await this.fetchWebConfig(); 
		return this.vapidPublicKey || null;
	}

	/**
	 * Register on message handler
	 *
	 * @param {function(
	 *  {
	 *    data:{
	 *       title: string,
	 *       body: string,
	 *       click_action: string|null,
	 *    }
	 *  }
	 * )} callback - Callback function to handle message
	 */
	onMessage(callback) {
		if (callback == null) return;
		this.onMessageHandler = callback;
		if (this.messaging == null || !this.initialized) return;
		onFCMMessage(this.messaging, this.onMessageHandler);
	}

	/**
	 * Check if notification is enabled
	 *
	 * @returns {boolean}
	 */
	isNotificationEnabled() {
		return localStorage.getItem(`firebase_token_${this.projectName}`) !== null;
	}

	/**
	 * Enable notification
	 * This will return notification permission status and token
	 *
	 * @returns {Promise<{permission_granted: boolean, token: string | null}>}
	 */
	async enableNotification() {
		if (!(await isSupported())) {
			throw new Error("Push notifications are not supported on your device.");
		}
		if (!this.initialized && this.serviceWorkerRegistration) {
			console.warn("[FrappePushNotification] Not initialized. Attempting to initialize now before enabling notifications...");
			await this.initialize(this.serviceWorkerRegistration); // Try to initialize if not already
		}
		if (!this.initialized) {
			throw new Error("FrappePushNotification not initialized. Cannot enable notifications.");
		}
		if (!this.messaging) {
			throw new Error("Firebase Messaging not initialized. Cannot enable notifications.");
		}

		if (this.token) {
			return { permission_granted: true, token: this.token };
		}

		const permission = await Notification.requestPermission();
		if (permission !== "granted") {
			return { permission_granted: false, token: null };
		}

		let oldToken = localStorage.getItem(`firebase_token_${this.projectName}`);
		if (!this.vapidPublicKey) {
			console.error("[FrappePushNotification] VAPID public key is missing. Cannot get FCM token.");
			throw new Error("VAPID public key not available. Cannot get FCM token.");
		}

		let newToken = await getToken(this.messaging, {
			vapidKey: this.vapidPublicKey,
			serviceWorkerRegistration: this.serviceWorkerRegistration // Use the PWA SW for token scope
		});

		if (oldToken !== newToken) {
			if (oldToken) {
				await this.unregisterTokenHandler(oldToken);
			}
			let isSubscriptionSuccessful = await this.registerTokenHandler(newToken);
			if (!isSubscriptionSuccessful) {
				throw new Error("Failed to subscribe to push notification with backend.");
			}
			localStorage.setItem(`firebase_token_${this.projectName}`, newToken);
		}
		this.token = newToken;
		return { permission_granted: true, token: newToken };
	}

	/**
	 * Disable notification
	 * This will delete token from firebase and unsubscribe from push notification
	 *
	 * @returns {Promise<void>}
	 */
	async disableNotification() {
		if (!this.initialized && this.serviceWorkerRegistration) {
			// Try to initialize to get messaging instance for token deletion
			try { await this.initialize(this.serviceWorkerRegistration); } catch(e) { /* ignore if fails */}
		}

		let currentToken = this.token || localStorage.getItem(`firebase_token_${this.projectName}`);
		if (!currentToken) return;

		if (this.messaging) {
			try {
				await deleteToken(this.messaging);
				console.log("[FrappePushNotification] Token deleted from Firebase.");
			} catch (e) {
				console.error("[FrappePushNotification] Failed to delete token from Firebase: ", e);
			}
		} else {
			console.warn("[FrappePushNotification] Firebase Messaging not available; cannot delete token from Firebase directly.");
		}

		try {
			await this.unregisterTokenHandler(currentToken);
		} catch (e) { /* Error already logged by unregisterTokenHandler */ }
		localStorage.removeItem(`firebase_token_${this.projectName}`);
		this.token = null;
	}

	/**
	 * Register Token Handler
	 *
	 * @param {string} token - FCM token
	 * @returns {Promise<boolean>}
	 */
	async registerTokenHandler(token) {
		try {
			let response = await fetch(
				`${FrappePushNotification.relayServerBaseURL}/api/method/frappe.push_notification.subscribe?fcm_token=${token}&project_name=${this.projectName}`
			);
			if (!response.ok) {
				const errorText = await response.text();
				console.error(`[FrappePushNotification] Backend subscription failed: ${response.status}. Response: ${errorText}`);
				return false;
			}
			let response_json = await response.json();
			// Assuming successful response has a truthy message or specific success indicator
			if (response_json.message && response_json.message === "Subscribed") { // Or check for a specific success status if API provides one
				console.log("[FrappePushNotification] Token registered with backend successfully.");
				return true;
			}
			console.error("[FrappePushNotification] Backend subscription response indicates failure:", response_json);
			return false;
		} catch (e) {
			console.error("[FrappePushNotification] Error registering token with backend: ", e);
			return false;
		}
	}

	/**
	 * Unregister token Handler
	 *
	 * @param {string} token - FCM token
	 * @returns {Promise<boolean>}
	 */
	async unregisterTokenHandler(token) {
		try {
			let response = await fetch(
				`${FrappePushNotification.relayServerBaseURL}/api/method/frappe.push_notification.unsubscribe?fcm_token=${token}&project_name=${this.projectName}`
			);
			if (!response.ok) {
				const errorText = await response.text();
				console.error(`[FrappePushNotification] Backend unsubscription failed: ${response.status}. Response: ${errorText}`);
				return false;
			}
			let response_json = await response.json();
			if (response_json.message && response_json.message === "Unsubscribed") { // Or check for a specific success status
				console.log("[FrappePushNotification] Token unregistered from backend successfully.");
				return true;
			}
			console.error("[FrappePushNotification] Backend unsubscription response indicates failure:", response_json);
			return false;
		} catch (e) {
			console.error("[FrappePushNotification] Error unregistering token with backend: ", e);
			return false;
		}
	}
} 