// Frappe Push Notification Client
class FrappePushNotification {
    constructor(projectName) {
        this.projectName = projectName;
        this.token = localStorage.getItem(`firebase_token_${projectName}`);
        this.relayServerBaseURL = window.frappe?.boot.push_relay_server_url;
    }

    async initialize(serviceWorkerRegistration) {
        if (!this.relayServerBaseURL) return;

        try {
            const webConfig = await this.fetchWebConfig();
            const vapidKey = await this.fetchVapidPublicKey();

            const firebaseApp = firebase.initializeApp(webConfig);
            this.messaging = firebase.messaging(firebaseApp);

            // Set up foreground message handler
            this.messaging.onMessage((payload) => {
                if (this.onMessage) {
                    this.onMessage(payload);
                }
            });

            // If we have a token, register it
            if (this.token) {
                await this.registerTokenHandler(this.token);
            }
        } catch (error) {
            console.error("Failed to initialize push notifications:", error);
        }
    }

    async fetchWebConfig() {
        const response = await fetch(
            `${this.relayServerBaseURL}/api/method/notification_relay.api.get_config?project_name=${this.projectName}`
        );
        const data = await response.json();
        return data.message.web_config;
    }

    async fetchVapidPublicKey() {
        const response = await fetch(
            `${this.relayServerBaseURL}/api/method/notification_relay.api.get_config?project_name=${this.projectName}`
        );
        const data = await response.json();
        return data.message.vapid_public_key;
    }

    async enableNotification() {
        if (!("Notification" in window)) {
            throw new Error("This browser does not support notifications");
        }

        const permission = await Notification.requestPermission();
        if (permission !== "granted") {
            throw new Error("Notification permission denied");
        }

        const vapidKey = await this.fetchVapidPublicKey();
        const serviceWorkerRegistration = await navigator.serviceWorker.ready;
        
        const newToken = await this.messaging.getToken({
            vapidKey,
            serviceWorkerRegistration,
        });

        if (this.token && this.token !== newToken) {
            await this.unregisterTokenHandler(this.token);
        }

        await this.registerTokenHandler(newToken);
        this.token = newToken;
        localStorage.setItem(`firebase_token_${this.projectName}`, newToken);
    }

    async disableNotification() {
        if (this.token) {
            await this.messaging.deleteToken();
            await this.unregisterTokenHandler(this.token);
            localStorage.removeItem(`firebase_token_${this.projectName}`);
            this.token = null;
        }
    }

    async registerTokenHandler(token) {
        await fetch(
            `/api/method/frappe.push_notification.subscribe?fcm_token=${token}&project_name=${this.projectName}`
        );
    }

    async unregisterTokenHandler(token) {
        await fetch(
            `/api/method/frappe.push_notification.unsubscribe?fcm_token=${token}&project_name=${this.projectName}`
        );
    }

    isNotificationEnabled() {
        return !!this.token;
    }
} 