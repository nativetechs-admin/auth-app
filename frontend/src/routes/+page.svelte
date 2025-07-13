<script lang="ts">
	/**
	 * Home Page Component
	 * Landing page with authentication-aware content
	 */

	import { isAuthenticated, currentUser } from '../lib/auth/authStore';
	import LoginButton from '../lib/components/LoginButton.svelte';

	// Reactive statements
	$: user = $currentUser;
</script>

<svelte:head>
	<title>Home - SSO Application</title>
</svelte:head>

<div class="home-container">
	<div class="hero-section">
		<h1 class="hero-title">
			{#if $isAuthenticated && user}
				Welcome back, {user.given_name || user.name}!
			{:else}
				Welcome to SSO Application
			{/if}
		</h1>
		
		<p class="hero-subtitle">
			{#if $isAuthenticated}
				You are successfully authenticated with Microsoft Entra ID.
			{:else}
				Secure Single Sign-On with Microsoft Entra ID integration.
			{/if}
		</p>

		{#if !$isAuthenticated}
			<div class="hero-actions">
				<LoginButton size="lg" />
			</div>
		{:else}
			<div class="hero-actions">
				<a href="/dashboard" class="dashboard-btn">
					Go to Dashboard
				</a>
			</div>
		{/if}
	</div>

	<div class="features-section">
		<h2>Features</h2>
		<div class="features-grid">
			<div class="feature-card">
				<div class="feature-icon">🔐</div>
				<h3>Secure Authentication</h3>
				<p>Enterprise-grade security with Microsoft Entra ID integration and PKCE flow.</p>
			</div>
			<div class="feature-card">
				<div class="feature-icon">⚡</div>
				<h3>Modern Frontend</h3>
				<p>Built with SvelteKit and TypeScript for optimal performance and developer experience.</p>
			</div>
			<div class="feature-card">
				<div class="feature-icon">🔄</div>
				<h3>Automatic Token Refresh</h3>
				<p>Seamless token management with automatic refresh and secure storage.</p>
			</div>
			<div class="feature-card">
				<div class="feature-icon">☁️</div>
				<h3>Azure Integration</h3>
				<p>Native Azure deployment with best practices for scalability and security.</p>
			</div>
		</div>
	</div>
</div>

<style>
	.home-container {
		max-width: 800px;
		margin: 0 auto;
	}

	.hero-section {
		text-align: center;
		padding: 4rem 0;
	}

	.hero-title {
		font-size: 3rem;
		font-weight: 700;
		color: #111827;
		margin: 0 0 1.5rem 0;
		line-height: 1.1;
	}

	.hero-subtitle {
		font-size: 1.25rem;
		color: #6b7280;
		margin: 0 0 2.5rem 0;
		line-height: 1.5;
	}

	.hero-actions {
		display: flex;
		justify-content: center;
		gap: 1rem;
	}

	.dashboard-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 1rem 2rem;
		background-color: #0066cc;
		color: white;
		text-decoration: none;
		border-radius: 0.375rem;
		font-size: 1.125rem;
		font-weight: 500;
		transition: background-color 0.2s ease-in-out;
	}

	.dashboard-btn:hover {
		background-color: #0052a3;
	}

	.features-section {
		padding: 4rem 0;
	}

	.features-section h2 {
		text-align: center;
		font-size: 2rem;
		font-weight: 600;
		color: #111827;
		margin: 0 0 3rem 0;
	}

	.features-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 2rem;
	}

	.feature-card {
		background: white;
		padding: 2rem;
		border-radius: 0.5rem;
		box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
		text-align: center;
	}

	.feature-icon {
		font-size: 2.5rem;
		margin-bottom: 1rem;
	}

	.feature-card h3 {
		font-size: 1.25rem;
		font-weight: 600;
		color: #111827;
		margin: 0 0 1rem 0;
	}

	.feature-card p {
		color: #6b7280;
		line-height: 1.5;
		margin: 0;
	}

	/* Responsive design */
	@media (max-width: 768px) {
		.hero-title {
			font-size: 2rem;
		}

		.hero-subtitle {
			font-size: 1.125rem;
		}

		.hero-section {
			padding: 2rem 0;
		}

		.features-section {
			padding: 2rem 0;
		}

		.features-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
