<script lang="ts">
	/**
	 * Login Page Component
	 * Dedicated login page with error handling
	 */

	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { isAuthenticated, authError } from '../../lib/auth/authStore';
	import LoginButton from '../../lib/components/LoginButton.svelte';

	// Local state
	let mounted = false;
	let errorMessage = '';

	onMount(() => {
		mounted = true;

		// Check for error in URL params
		const urlError = $page.url.searchParams.get('error');
		if (urlError) {
			errorMessage = decodeURIComponent(urlError);
		}

		// Redirect if already authenticated
		if ($isAuthenticated) {
			const returnUrl = $page.url.searchParams.get('return_url') || '/dashboard';
			goto(decodeURIComponent(returnUrl));
		}
	});

	// Reactive statements
	$: if (mounted && $isAuthenticated) {
		const returnUrl = $page.url.searchParams.get('return_url') || '/dashboard';
		goto(decodeURIComponent(returnUrl));
	}

	$: displayError = errorMessage || $authError;
</script>

<svelte:head>
	<title>Sign In - SSO Application</title>
</svelte:head>

<div class="login-container">
	<div class="login-card">
		<div class="login-header">
			<h1>Sign In</h1>
			<p>Access your account with Microsoft Entra ID</p>
		</div>

		{#if displayError}
			<div class="error-alert" role="alert">
				<svg class="error-icon" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
				</svg>
				<div>
					<h3>Authentication Error</h3>
					<p>{displayError}</p>
				</div>
			</div>
		{/if}

		<div class="login-form">
			<LoginButton size="lg" variant="primary" />
		</div>

		<div class="login-info">
			<h3>Secure Authentication</h3>
			<ul>
				<li>✓ Enterprise-grade security with Microsoft Entra ID</li>
				<li>✓ PKCE flow for enhanced protection</li>
				<li>✓ Automatic token management</li>
				<li>✓ Secure session handling</li>
			</ul>
		</div>

		<div class="login-footer">
			<p>
				Need help? Contact your system administrator or 
				<a href="mailto:support@company.com">support@company.com</a>
			</p>
		</div>
	</div>
</div>

<style>
	.login-container {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: calc(100vh - 200px);
		padding: 2rem;
	}

	.login-card {
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
		padding: 3rem;
		max-width: 480px;
		width: 100%;
	}

	.login-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.login-header h1 {
		font-size: 2rem;
		font-weight: 700;
		color: #111827;
		margin: 0 0 0.5rem 0;
	}

	.login-header p {
		color: #6b7280;
		margin: 0;
		font-size: 1rem;
	}

	.error-alert {
		display: flex;
		gap: 0.75rem;
		padding: 1rem;
		background-color: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 0.5rem;
		margin-bottom: 2rem;
		color: #dc2626;
	}

	.error-icon {
		width: 1.5rem;
		height: 1.5rem;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}

	.error-alert h3 {
		font-size: 1rem;
		font-weight: 600;
		margin: 0 0 0.25rem 0;
	}

	.error-alert p {
		font-size: 0.875rem;
		margin: 0;
		line-height: 1.4;
	}

	.login-form {
		display: flex;
		justify-content: center;
		margin-bottom: 2rem;
	}

	.login-info {
		background-color: #f9fafb;
		border-radius: 0.5rem;
		padding: 1.5rem;
		margin-bottom: 2rem;
	}

	.login-info h3 {
		font-size: 1.125rem;
		font-weight: 600;
		color: #111827;
		margin: 0 0 1rem 0;
	}

	.login-info ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.login-info li {
		color: #374151;
		margin-bottom: 0.5rem;
		font-size: 0.875rem;
	}

	.login-info li:last-child {
		margin-bottom: 0;
	}

	.login-footer {
		text-align: center;
		font-size: 0.875rem;
		color: #6b7280;
	}

	.login-footer p {
		margin: 0;
		line-height: 1.5;
	}

	.login-footer a {
		color: #0066cc;
		text-decoration: none;
	}

	.login-footer a:hover {
		text-decoration: underline;
	}

	/* Responsive design */
	@media (max-width: 640px) {
		.login-container {
			padding: 1rem;
		}

		.login-card {
			padding: 2rem;
		}

		.login-header h1 {
			font-size: 1.75rem;
		}
	}
</style>
