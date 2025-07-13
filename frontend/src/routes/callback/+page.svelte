<script lang="ts">
	/**
	 * Auth Callback Page Component
	 * Handles the OAuth callback from Azure AD
	 */

	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { AuthService } from '../../lib/auth/authService';
	import { authLoading, authError } from '../../lib/auth/authStore';

	// Define API base URL
	const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin.replace(':5173', ':8000');

	// Local state
	let processingCallback = true;
	let callbackError = '';

	onMount(async () => {
		try {
			processingCallback = true;
			
			// Get URL parameters
			const urlParams = new URLSearchParams(window.location.search);
			const successToken = urlParams.get('success_token');
			
			if (!successToken) {
				callbackError = 'No success token found in callback URL';
				processingCallback = false;
				return;
			}
			
			// Use AuthService to handle callback with cookieless approach
			const success = await AuthService.handleCallback(successToken);
			
			if (!success) {
				throw new Error('Failed to complete authentication');
			}

			processingCallback = false;
			goto('/dashboard');
			
		} catch (error) {
			callbackError = error instanceof Error ? error.message : 'Authentication failed';
			processingCallback = false;
		}
	});

	// Handle retry
	function handleRetry() {
		goto('/login');
	}
</script>

<svelte:head>
	<title>Processing Authentication - SSO Application</title>
</svelte:head>

<div class="callback-container">
	{#if processingCallback && !callbackError && !$authError}
		<div class="processing-card">
			<div class="spinner-container">
				<svg class="spinner" viewBox="0 0 24 24">
					<circle
						cx="12"
						cy="12"
						r="10"
						stroke="currentColor"
						stroke-width="2"
						fill="none"
						stroke-dasharray="31.416"
						stroke-dashoffset="31.416"
					/>
				</svg>
			</div>
			<h2>Processing Authentication</h2>
			<p>Please wait while we verify your credentials...</p>
			<div class="progress-steps">
				<div class="step completed">
					<div class="step-indicator">✓</div>
					<span>Redirected from Microsoft</span>
				</div>
				<div class="step active">
					<div class="step-indicator">
						<div class="mini-spinner"></div>
					</div>
					<span>Validating credentials</span>
				</div>
				<div class="step">
					<div class="step-indicator">3</div>
					<span>Redirecting to dashboard</span>
				</div>
			</div>
		</div>
	{:else if callbackError || $authError}
		<div class="error-card">
			<div class="error-icon-container">
				<svg class="error-icon" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
				</svg>
			</div>
			<h2>Authentication Failed</h2>
			<p class="error-message">
				{callbackError || $authError}
			</p>
			<div class="error-actions">
				<button class="retry-btn" on:click={handleRetry}>
					Try Again
				</button>
				<a href="/" class="home-link">
					Go Home
				</a>
			</div>
		</div>
	{/if}
</div>

<style>
	.callback-container {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: calc(100vh - 200px);
		padding: 2rem;
	}

	.processing-card,
	.error-card {
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
		padding: 3rem;
		max-width: 500px;
		width: 100%;
		text-align: center;
	}

	.spinner-container {
		margin-bottom: 2rem;
	}

	.spinner {
		width: 3rem;
		height: 3rem;
		color: #0066cc;
		animation: spin 1s linear infinite;
	}

	.error-icon-container {
		margin-bottom: 2rem;
	}

	.error-icon {
		width: 3rem;
		height: 3rem;
		color: #dc2626;
	}

	h2 {
		font-size: 1.5rem;
		font-weight: 600;
		color: #111827;
		margin: 0 0 1rem 0;
	}

	p {
		color: #6b7280;
		margin: 0 0 2rem 0;
		line-height: 1.5;
	}

	.error-message {
		color: #dc2626;
		background-color: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 0.375rem;
		padding: 1rem;
		font-size: 0.875rem;
	}

	.progress-steps {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		text-align: left;
	}

	.step {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		opacity: 0.5;
	}

	.step.completed,
	.step.active {
		opacity: 1;
	}

	.step-indicator {
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
		font-weight: 600;
		flex-shrink: 0;
	}

	.step.completed .step-indicator {
		background-color: #10b981;
		color: white;
	}

	.step.active .step-indicator {
		background-color: #0066cc;
		color: white;
	}

	.step:not(.completed):not(.active) .step-indicator {
		background-color: #e5e7eb;
		color: #6b7280;
	}

	.mini-spinner {
		width: 1rem;
		height: 1rem;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top: 2px solid white;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.error-actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 2rem;
	}

	.retry-btn {
		background-color: #0066cc;
		color: white;
		border: none;
		border-radius: 0.375rem;
		padding: 0.75rem 1.5rem;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s ease-in-out;
		font-family: inherit;
	}

	.retry-btn:hover {
		background-color: #0052a3;
	}

	.retry-btn:focus {
		outline: 2px solid #0066cc;
		outline-offset: 2px;
	}

	.home-link {
		color: #6b7280;
		text-decoration: none;
		padding: 0.75rem 1.5rem;
		border-radius: 0.375rem;
		transition: color 0.2s ease-in-out;
	}

	.home-link:hover {
		color: #374151;
		background-color: #f9fafb;
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	/* Responsive design */
	@media (max-width: 640px) {
		.callback-container {
			padding: 1rem;
		}

		.processing-card,
		.error-card {
			padding: 2rem;
		}

		.error-actions {
			flex-direction: column;
		}
	}
</style>
