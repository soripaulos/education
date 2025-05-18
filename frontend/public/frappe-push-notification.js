import { initializeApp } from "firebase/app"
import {
	getMessaging,
	getToken,
	isSupported,
	deleteToken,
	onMessage as onFCMMessage,
} from "firebase/messaging"

class FrappePushNotification {
	static get relayServerBaseURL() {
		return window.frappe?.boot.push_relay_server_url
	}

	/**
	 * Constructor
	 *
	 * @param {string} projectName
	 */
	constructor(projectName) {
		// client info
		this.projectName = projectName
		this.webConfig = null
		this.vapidPublicKey = ""
		this.token = null

		// state
		this.initialized = false
		this.messaging = null
		this.serviceWorkerRegistration = null

		// event handlers
		this.onMessageHandler = null
	}

	/**
	 * Initialize notification service client
	 *
	 * @param {ServiceWorkerRegistration} serviceWorkerRegistration - Service worker registration object
	 * @returns {Promise<void>}
	 */
	async initialize(serviceWorkerRegistration) {
		if (this.initialized) {
			return
		}
		this.serviceWorkerRegistration = serviceWorkerRegistration
		const config = await this.fetchWebConfig()
		this.messaging = getMessaging(initializeApp(config))
		this.onMessage(this.onMessageHandler)
		this.initialized = true
	}

	/**
	 * Fetch web config of the project
	 *
	 * @returns {Promise<object>}
	 */
	async fetchWebConfig() {
		if (this.webConfig !== null && this.webConfig !== undefined) {
			return this.webConfig
		}
		try {
			let url = `${FrappePushNotification.relayServerBaseURL}/api/method/notification_relay.api.get_config?project_name=${this.projectName}`
			let response = await fetch(url)
			let response_json = await response.json()
			this.webConfig = response_json.message.web_config
			return this.webConfig
		} catch (e) {
			throw new Error(
				"Push Notification Relay is not configured properly on your site."
			)
		}
	}

	/**
	 * Fetch VAPID public key
	 *
	 * @returns {Promise<string>}
	 */
	async fetchVapidPublicKey() {
		if (this.vapidPublicKey !== "") {
			return this.vapidPublicKey
		}
		try {
			let url = `${FrappePushNotification.relayServerBaseURL}/api/method/notification_relay.api.get_config?project_name=${this.projectName}`
			let response = await fetch(url)
			let response_json = await response.json()
			this.vapidPublicKey = response_json.message.vapid_public_key
			return this.vapidPublicKey
		} catch (e) {
			throw new Error(
				"Push Notification Relay is not configured properly on your site."
			)
		}
	}

	/**
	 * Register on message handler
	 *
	 * @param {function} callback - Callback function to handle message
	 */
	onMessage(callback) {
		if (callback == null) return
		this.onMessageHandler = callback
		if (this.messaging == null) return
		onFCMMessage(this.messaging, this.onMessageHandler)
	}

	/**
	 * Check if notification is enabled
	 *
	 * @returns {boolean}
	 */
	isNotificationEnabled() {
		return localStorage.getItem(`firebase_token_${this.projectName}`) !== null
	}

	/**
	 * Enable notification
	 * This will return notification permission status and token
	 */
	async enableNotification() {
		if (!(await isSupported())) {
			throw new Error("Push notifications are not supported on your device")
		}
		// Return if token already presence in the instance
		if (this.token != null) {
			return {
				permission_granted: true,
				token: this.token,
			}
		}
		// ask for permission
		const permission = await Notification.requestPermission()
		if (permission !== "granted") {
			return {
				permission_granted: false,
				token: "",
			}
		}
		// check in local storage for old token
		let oldToken = localStorage.getItem(`firebase_token_${this.projectName}`)
		const vapidKey = await this.fetchVapidPublicKey()
		let newToken = await getToken(this.messaging, {
			vapidKey: vapidKey,
			serviceWorkerRegistration: this.serviceWorkerRegistration,
		})
		// register new token if token is changed
		if (oldToken !== newToken) {
			// unsubscribe old token
			if (oldToken) {
				await this.unregisterTokenHandler(oldToken)
			}
			// subscribe push notification and register token
			let isSubscriptionSuccessful = await this.registerTokenHandler(newToken)
			if (isSubscriptionSuccessful === false) {
				throw new Error("Failed to subscribe to push notification")
			}
			// save token to local storage
			localStorage.setItem(`firebase_token_${this.projectName}`, newToken)
		}
		this.token = newToken
		return {
			permission_granted: true,
			token: newToken,
		}
	}

	/**
	 * Disable notification
	 * This will delete token from firebase and unsubscribe from push notification
	 */
	async disableNotification() {
		if (this.token == null) {
			// try to fetch token from local storage
			this.token = localStorage.getItem(`firebase_token_${this.projectName}`)
			if (this.token == null || this.token === "") {
				return
			}
		}
		// delete old token from firebase
		try {
			await deleteToken(this.messaging)
		} catch (e) {
			console.error("Failed to delete token from firebase")
		}
		try {
			await this.unregisterTokenHandler(this.token)
		} catch (e) {
			console.error("Failed to unsubscribe from push notification")
		}
		// remove token
		localStorage.removeItem(`firebase_token_${this.projectName}`)
		this.token = null
	}

	/**
	 * Register Token Handler
	 *
	 * @param {string} token - FCM token
	 */
	async registerTokenHandler(token) {
		try {
			await fetch(
				`/api/method/frappe.push_notification.subscribe?fcm_token=${token}&project_name=${this.projectName}`
			)
			return true
		} catch (e) {
			console.error("Failed to register token", e)
			return false
		}
	}

	/**
	 * Unregister Token Handler
	 *
	 * @param {string} token - FCM token
	 */
	async unregisterTokenHandler(token) {
		try {
			await fetch(
				`/api/method/frappe.push_notification.unsubscribe?fcm_token=${token}&project_name=${this.projectName}`
			)
			return true
		} catch (e) {
			console.error("Failed to unregister token", e)
			return false
		}
	}
}

export default FrappePushNotification 