<script lang="ts">
	/**
	 * Dashboard Page Component
	 * Protected dashboard showing user information and application features
	 */

	import { onMount } from 'svelte';
	import ProtectedRoute from '../../lib/components/ProtectedRoute.svelte';
	import { currentUser } from '../../lib/auth/authStore';
	import type { User } from '../../lib/auth/types';

	// Local state
	let loading = false; // No API call needed, user data is in store
	let error = '';

	// onMount is not needed since we're using the store data
	// The user data is already loaded during authentication

	// Reactive statements
	$: user = $currentUser;
	$: profileData = $currentUser; // Use the same data from the store

	// Helper functions
	function formatDate(dateString: string | undefined): string {
		if (!dateString) return 'Not available';
		return new Intl.DateTimeFormat('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		}).format(new Date(dateString));
	}

	function getStatusBadge(isActive: boolean): string {
		return 'ACTIVE'; // Always show as active for authenticated users
	}

	function getStatusColor(isActive: boolean): string {
		return 'status-active'; // Always show active color for authenticated users
	}
</script>

<svelte:head>
	<title>Dashboard - SSO Application</title>
</svelte:head>

<ProtectedRoute>
	<div class="dashboard-container">
		<div class="dashboard-header">
			<h1>Dashboard</h1>
			<p>Welcome to your secure dashboard</p>
		</div>

		{#if user}
			<div class="dashboard-grid">
				<!-- User Profile Card -->
				<div class="card profile-card">
					<div class="card-header">
						<h2>Profile Information</h2>
						<span class="status-badge {getStatusColor(user.is_active)}">
							{getStatusBadge(user.is_active)}
						</span>
					</div>
					<div class="card-content">
						<div class="profile-section">
							<div class="profile-avatar">
								{#if user.profile_picture}
									<img src={user.profile_picture} alt={user.name} />
								{:else}
									<div class="avatar-placeholder">
										{user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
									</div>
								{/if}
							</div>
							<div class="profile-details">
								<h3>{user.name}</h3>
								<p class="email">{user.email}</p>
								{#if user.job_title}
									<p class="job-title">{user.job_title}</p>
								{/if}
								{#if user.department}
									<p class="department">{user.department}</p>
								{/if}
							</div>
						</div>
					</div>
				</div>

				<!-- Account Details Card -->
				<div class="card details-card">
					<div class="card-header">
						<h2>Account Details</h2>
					</div>
					<div class="card-content">
						<div class="detail-grid">
							<div class="detail-item">
								<label>Email:</label>
								<span>{user.email}</span>
							</div>
							<div class="detail-item">
								<label>Display Name:</label>
								<span>{user.name}</span>
							</div>
							<div class="detail-item">
								<label>Previous Login:</label>
								<span>Not available</span>
							</div>
							<div class="detail-item">
								<label>Account Status:</label>
								<span class="status-text active">Active</span>
							</div>
						</div>
					</div>
				</div>

				<!-- Session Information Card -->
				<div class="card session-card">
					<div class="card-header">
						<h2>Session Information</h2>
					</div>
					<div class="card-content">
						<div class="session-info">
							<div class="session-item">
								<span class="session-icon">🔐</span>
								<div>
									<h4>Secure Authentication</h4>
									<p>Authenticated via Microsoft Entra ID</p>
								</div>
							</div>
							<div class="session-item">
								<span class="session-icon">�</span>
								<div>
									<h4>Session Tracking</h4>
									<p>Activity logged in Microsoft Dataverse</p>
								</div>
							</div>
							<div class="session-item">
								<span class="session-icon">🛡️</span>
								<div>
									<h4>Token Security</h4>
									<p>Cookieless authentication with local storage</p>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Quick Actions Card -->
				<div class="card actions-card">
					<div class="card-header">
						<h2>Quick Actions</h2>
					</div>
					<div class="card-content">
						<div class="action-buttons">
							<button class="action-btn primary" on:click={() => console.log('My Projects clicked - navigation not implemented yet')}>
								<span class="action-icon">�</span>
								My Projects
							</button>
						</div>
					</div>
				</div>
			</div>

			{#if loading}
				<div class="loading-overlay">
					<div class="spinner"></div>
					<p>Loading additional profile data...</p>
				</div>
			{/if}

			{#if error}
				<div class="error-notice">
					<p>{error}</p>
				</div>
			{/if}
		{/if}
	</div>
</ProtectedRoute>

<style>
	.dashboard-container {
		max-width: 1200px;
		margin: 0 auto;
	}

	.dashboard-header {
		margin-bottom: 2rem;
	}

	.dashboard-header h1 {
		font-size: 2.5rem;
		font-weight: 700;
		color: #111827;
		margin: 0 0 0.5rem 0;
	}

	.dashboard-header p {
		color: #6b7280;
		font-size: 1.125rem;
		margin: 0;
	}

	.dashboard-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
		gap: 2rem;
	}

	.card {
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
		overflow: hidden;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		border-bottom: 1px solid #e5e7eb;
		background-color: #f9fafb;
	}

	.card-header h2 {
		font-size: 1.25rem;
		font-weight: 600;
		color: #111827;
		margin: 0;
	}

	.card-content {
		padding: 1.5rem;
	}

	.status-badge {
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.status-active {
		background-color: #d1fae5;
		color: #065f46;
	}

	.status-inactive {
		background-color: #fee2e2;
		color: #991b1b;
	}

	.profile-section {
		display: flex;
		gap: 1.5rem;
		align-items: center;
	}

	.profile-avatar img,
	.avatar-placeholder {
		width: 4rem;
		height: 4rem;
		border-radius: 50%;
	}

	.avatar-placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
		background-color: #0066cc;
		color: white;
		font-weight: 600;
		font-size: 1.25rem;
	}

	.profile-details h3 {
		font-size: 1.5rem;
		font-weight: 600;
		color: #111827;
		margin: 0 0 0.5rem 0;
	}

	.email {
		color: #6b7280;
		font-size: 1rem;
		margin: 0 0 0.25rem 0;
	}

	.job-title,
	.department {
		color: #374151;
		font-size: 0.875rem;
		margin: 0.125rem 0;
	}

	.detail-grid {
		display: grid;
		gap: 1rem;
	}

	.detail-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 0;
		border-bottom: 1px solid #f3f4f6;
	}

	.detail-item:last-child {
		border-bottom: none;
	}

	.detail-item label {
		font-weight: 500;
		color: #374151;
	}

	.detail-item span {
		color: #6b7280;
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		font-size: 0.875rem;
		text-align: right;
		max-width: 60%;
		word-break: break-all;
	}

	.status-text {
		font-family: inherit !important;
		font-weight: 600 !important;
	}

	.status-text.active {
		color: #10b981 !important;
	}

	.session-info {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.session-item {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	.session-icon {
		font-size: 1.5rem;
		flex-shrink: 0;
	}

	.session-item h4 {
		font-size: 1rem;
		font-weight: 600;
		color: #111827;
		margin: 0 0 0.25rem 0;
	}

	.session-item p {
		color: #6b7280;
		font-size: 0.875rem;
		margin: 0;
	}

	.action-buttons {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
		gap: 1rem;
	}

	.action-btn {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 1rem;
		border: none;
		border-radius: 0.5rem;
		cursor: pointer;
		transition: all 0.2s ease-in-out;
		font-family: inherit;
		font-size: 0.875rem;
		font-weight: 500;
	}

	.action-btn.primary {
		background-color: #0066cc;
		color: white;
	}

	.action-btn.primary:hover {
		background-color: #0052a3;
	}

	.action-btn.secondary {
		background-color: #f3f4f6;
		color: #374151;
	}

	.action-btn.secondary:hover {
		background-color: #e5e7eb;
	}

	.action-icon {
		font-size: 1.25rem;
	}

	.loading-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		color: white;
	}

	.spinner {
		width: 2rem;
		height: 2rem;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top: 2px solid white;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 1rem;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.error-notice {
		background-color: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 0.5rem;
		padding: 1rem;
		margin-top: 2rem;
		color: #dc2626;
	}

	/* Responsive design */
	@media (max-width: 768px) {
		.dashboard-grid {
			grid-template-columns: 1fr;
		}

		.profile-section {
			flex-direction: column;
			text-align: center;
		}

		.detail-item {
			flex-direction: column;
			align-items: flex-start;
			gap: 0.25rem;
		}

		.detail-item span {
			max-width: 100%;
			text-align: left;
		}

		.action-buttons {
			grid-template-columns: repeat(2, 1fr);
		}
	}
</style>
