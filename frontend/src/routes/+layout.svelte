<script lang="ts">
	/**
	 * Root Layout Component
	 * Handles authentication initialization and global state management
	 */

	import { onMount } from 'svelte';
	import { AuthService } from '../lib/auth/authService';
	import { authLoading, isAuthenticated } from '../lib/auth/authStore';
	import '../app.css';

	// Initialize authentication on app load
	onMount(async () => {
		await AuthService.initializeAuth();
	});
</script>

<svelte:head>
	<title>SSO Application</title>
	<meta name="description" content="Secure Single Sign-On Application with Microsoft Entra ID" />
</svelte:head>

<div class="app">
	<header class="header">
		<nav class="nav">
			<div class="nav-brand">
				<a href="/" class="brand-link">
					<h1>SSO App</h1>
				</a>
			</div>
			
			<div class="nav-links">
				{#if $isAuthenticated}
					<a href="/dashboard" class="nav-link">Dashboard</a>
				{/if}
			</div>

			<div class="nav-actions">
				{#if !$authLoading}
					{#if $isAuthenticated}
						{#await import('../lib/components/UserProfile.svelte') then { default: UserProfile }}
							<UserProfile />
						{/await}
					{/if}
				{/if}
			</div>
		</nav>
	</header>

	<main class="main">
		<slot />
	</main>

	<footer class="footer">
		<p>&copy; 2025 SSO Application. Built with SvelteKit and Azure.</p>
	</footer>
</div>

<style>
	:global(html) {
		height: 100%;
	}

	:global(body) {
		height: 100%;
		margin: 0;
		padding: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
		line-height: 1.5;
		color: #374151;
		background-color: #f9fafb;
	}

	:global(#svelte) {
		height: 100%;
	}

	.app {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	.header {
		background-color: white;
		border-bottom: 1px solid #e5e7eb;
		box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
	}

	.nav {
		display: flex;
		align-items: center;
		justify-content: space-between;
		max-width: 1200px;
		margin: 0 auto;
		padding: 1rem 1.5rem;
	}

	.nav-brand {
		flex-shrink: 0;
	}

	.brand-link {
		text-decoration: none;
		color: inherit;
	}

	.brand-link h1 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 700;
		color: #0066cc;
	}

	.nav-links {
		display: flex;
		gap: 1.5rem;
		margin-left: 2rem;
	}

	.nav-link {
		color: #374151;
		text-decoration: none;
		font-weight: 500;
		padding: 0.5rem 0;
		border-bottom: 2px solid transparent;
		transition: all 0.2s ease-in-out;
	}

	.nav-link:hover {
		color: #0066cc;
		border-bottom-color: #0066cc;
	}

	.nav-actions {
		flex-shrink: 0;
	}

	.main {
		flex: 1;
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem 1.5rem;
		width: 100%;
		box-sizing: border-box;
	}

	.footer {
		background-color: white;
		border-top: 1px solid #e5e7eb;
		padding: 1rem 1.5rem;
		text-align: center;
		color: #6b7280;
		font-size: 0.875rem;
	}

	.footer p {
		margin: 0;
	}

	/* Responsive design */
	@media (max-width: 768px) {
		.nav {
			flex-direction: column;
			gap: 1rem;
			align-items: stretch;
		}

		.nav-links {
			justify-content: center;
			margin-left: 0;
		}

		.nav-actions {
			align-self: center;
		}

		.main {
			padding: 1rem;
		}
	}
</style>
