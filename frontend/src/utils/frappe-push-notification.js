import { initializeApp } from "firebase/app";
import {
	getMessaging,
	getToken,
	isSupported,
	deleteToken,
	onMessage as onFCMMessage,
} from "firebase/messaging";

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
		
		// Try to get config from fetchWebConfig or use fallback config
		let config = await this.fetchWebConfig();
		
		// If the API call fails, use a hardcoded config for testing/development
		if (!config || Object.keys(config).length === 0) {
			console.warn("[FrappePushNotification] Using fallback Firebase config as API call failed.");
			// Fallback Firebase config - Replace with your real Firebase config before production
			config = {
				apiKey: "AIzaSyDummyKeyF1rebase123456",
				authDomain: "education-portal-placeholder.firebaseapp.com",
				projectId: "education-portal-placeholder",
				storageBucket: "education-portal-placeholder.appspot.com",
				messagingSenderId: "123456789012",
				appId: "1:123456789012:web:a1b2c3d4e5f6a7b8c9d0e1"
			};
			
			// Placeholder VAPID key - Replace with your real VAPID key
			this.vapidPublicKey = "BBQVWTuagUPDYpCZxVcsjcTzyXwPTAmcgW9HhbcVnwvf1Cje7H8vk-KebOyUU0-N-4jN01fWh6kqCLrr6-0XZEU";
		}
		
		// Initialize Firebase even with fallback config
		this.messaging = getMessaging(initializeApp(config));
		this.onMessage(this.onMessageHandler);
		this.initialized = true;
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
		if (this.webConfig) { // Check if already fetched
			return this.webConfig;
		}
		try {
			const relayUrl = FrappePushNotification.relayServerBaseURL;
			
			// Make a request to the notification relay API
			let url = `${relayUrl}/api/method/notification_relay.api.get_config?project_name=${this.projectName}`;
			console.log("[FrappePushNotification] Attempting to fetch Firebase config from:", url);
			
			// Set a timeout to prevent hanging if server doesn't respond
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
			
			let response = await fetch(url, { signal: controller.signal });
			clearTimeout(timeoutId);
			
			if (!response.ok) {
				throw new Error(`Failed to fetch Firebase config: ${response.status} ${response.statusText}`);
			}
			
			let response_json = await response.json();
			if (!response_json.config || !response_json.vapid_public_key) {
				console.error("[FrappePushNotification] Fetched Firebase config is incomplete.", response_json);
				return null; // Changed to return null instead of throwing
			}
			
			this.webConfig = response_json.config;
			this.vapidPublicKey = response_json.vapid_public_key; // Also store VAPID key
			console.log("[FrappePushNotification] Successfully fetched Firebase config.");
			return this.webConfig;
		} catch (e) {
			console.error("[FrappePushNotification] Error fetching web config:", e);
			// Don't throw, but return null so caller can handle
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
		if (this.messaging == null) return;
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
		if (!this.serviceWorkerRegistration) {
			throw new Error("ServiceWorkerRegistration not provided. Initialize FrappePushNotification with it first.");
		}
		if (!this.messaging) {
			// This implies fetchWebConfig failed or initialize wasn't called properly
			await this.initialize(this.serviceWorkerRegistration); // Try to re-initialize if messaging is missing
			if (!this.messaging) {
				throw new Error("Firebase Messaging not initialized. Cannot enable notifications.");
			}
		}

		if (this.token != null) {
			return {
				permission_granted: true,
				token: this.token,
			};
		}
		const permission = await Notification.requestPermission();
		if (permission !== "granted") {
			return {
				permission_granted: false,
				token: null,
			};
		}
		let oldToken = localStorage.getItem(`firebase_token_${this.projectName}`);
		const vapidKey = await this.fetchVapidPublicKey();
		if (!vapidKey) {
			throw new Error("VAPID public key not available. Cannot get FCM token.");
		}
		let newToken = await getToken(this.messaging, {
			vapidKey: vapidKey,
			serviceWorkerRegistration: this.serviceWorkerRegistration,
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
		return {
			permission_granted: true,
			token: newToken,
		};
	}

	/**
	 * Disable notification
	 * This will delete token from firebase and unsubscribe from push notification
	 *
	 * @returns {Promise<void>}
	 */
	async disableNotification() {
		if (!this.messaging) {
			// Attempt to initialize if messaging is not available, 
			// as it's needed for deleteToken
			// This situation is less ideal, assumes config can be fetched.
			if (this.serviceWorkerRegistration) {
				try {
					const config = await this.fetchWebConfig();
					if (config && Object.keys(config).length > 0) {
						this.messaging = getMessaging(initializeApp(config));
					} else {
						console.warn("[FrappePushNotification] Cannot disable notification: Firebase messaging not initialized due to missing config.");
						// Fallback to just removing local token and unregistering with backend if possible
					}
				} catch (e) {
					console.warn("[FrappePushNotification] Error re-initializing messaging for disableNotification: ", e);
				}
			}
		}

		let currentToken = this.token || localStorage.getItem(`firebase_token_${this.projectName}`);
		if (!currentToken) {
			return; // No token to disable
		}

		if (this.messaging) {
			try {
				await deleteToken(this.messaging);
			} catch (e) {
				console.error("[FrappePushNotification] Failed to delete token from Firebase: ", e);
			}
		} else {
			console.warn("[FrappePushNotification] Firebase Messaging not available; cannot delete token from Firebase directly.");
		}

		try {
			await this.unregisterTokenHandler(currentToken);
		} catch (e) {
			console.error("[FrappePushNotification] Failed to unsubscribe from push notification backend: ", e);
		}
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
				`/api/method/frappe.push_notification.subscribe?fcm_token=${token}&project_name=${this.projectName}`
			);
			if (!response.ok) {
				console.error(`[FrappePushNotification] Backend subscription failed: ${response.status}`);
				return false;
			}
			let response_json = await response.json();
			return response_json.message === "Subscribed";
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
				`/api/method/frappe.push_notification.unsubscribe?fcm_token=${token}&project_name=${this.projectName}`
			);
			if (!response.ok) {
				console.error(`[FrappePushNotification] Backend unsubscription failed: ${response.status}`);
				return false;
			}
			let response_json = await response.json();
			return response_json.message === "Unsubscribed";
		} catch (e) {
			console.error("[FrappePushNotification] Error unregistering token with backend: ", e);
			return false;
		}
	}
} 