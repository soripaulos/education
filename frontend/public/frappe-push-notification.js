/**
 * This file serves as a shim to load the static implementation of FrappePushNotification.
 * It avoids using ES modules which causes build issues with Vite.
 */
export default class FrappePushNotification {
	constructor(projectName) {
		// Load the static implementation
		const script = document.createElement('script');
		script.src = '/assets/education/frontend/static/frappe-push-notification.js';
		document.head.appendChild(script);
		
		// Create a proxy to delegate to the static implementation once loaded
		return new Proxy({
			projectName,
			_implementation: null,
			_pendingCalls: [],
			_methods: [
				'initialize', 'fetchWebConfig', 'fetchVapidPublicKey', 'onMessage',
				'isNotificationEnabled', 'enableNotification', 'disableNotification',
				'registerTokenHandler', 'unregisterTokenHandler', 'appendConfigToServiceWorkerURL'
			]
		}, {
			get(target, prop) {
				// For method calls, either queue them if the implementation isn't loaded yet,
				// or forward them to the implementation
				if (target._methods.includes(prop)) {
					return async (...args) => {
						// If the implementation isn't loaded yet
						if (!window.FrappePushNotification) {
							// Wait for the implementation to load
							await new Promise(resolve => {
								const checkImpl = setInterval(() => {
									if (window.FrappePushNotification) {
										clearInterval(checkImpl);
										// Create the implementation
										target._implementation = new window.FrappePushNotification(target.projectName);
										resolve();
									}
								}, 100);
							});
						}
						
						// If this is the first time accessing the implementation, create it
						if (!target._implementation && window.FrappePushNotification) {
							target._implementation = new window.FrappePushNotification(target.projectName);
						}
						
						// Now we can call the method on the implementation
						if (target._implementation) {
							return target._implementation[prop](...args);
						}
						
						console.error(`Failed to call ${prop} on FrappePushNotification implementation`);
						return null;
					};
				}
				
				// For properties, just return them from the proxy
				return target[prop];
			}
		});
	}
} 