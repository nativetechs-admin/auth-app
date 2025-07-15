<script lang="ts">
	/**
	 * Dashboard Page Component
	 * Protected dashboard showing user information and application features
	 */

	import { goto } from '$app/navigation';
	import ProtectedRoute from '../../lib/components/ProtectedRoute.svelte';
	import { currentUser } from '../../lib/auth/authStore';

	// Reactive statements
	$: user = $currentUser;

	// Navigation functions
	function goToProjects() {
		goto('/projects');
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
						<span class="status-badge status-active">ACTIVE</span>
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
								<span class="detail-label">Email:</span>
								<span>{user.email}</span>
							</div>
							<div class="detail-item">
								<span class="detail-label">Display Name:</span>
								<span>{user.name}</span>
							</div>
							<div class="detail-item">
								<span class="detail-label">Account Status:</span>
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
								<span class="session-icon">📝</span>
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
							<button 
								class="action-btn primary" 
								on:click={goToProjects}
							>
								<span class="action-icon">📋</span>
								View My Projects
							</button>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
</ProtectedRoute>

<style>
	.dashboard-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
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

	.profile-section {
		display: flex;
		gap: 1.5rem;
		align-items: flex-start;
	}

	.profile-avatar {
		flex-shrink: 0;
	}

	.profile-avatar img {
		width: 4rem;
		height: 4rem;
		border-radius: 50%;
		object-fit: cover;
	}

	.avatar-placeholder {
		width: 4rem;
		height: 4rem;
		border-radius: 50%;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		font-weight: 600;
		font-size: 1.25rem;
	}

	.profile-details h3 {
		font-size: 1.375rem;
		font-weight: 600;
		color: #111827;
		margin: 0 0 0.5rem 0;
	}

	.profile-details .email {
		color: #6b7280;
		margin: 0 0 0.25rem 0;
	}

	.profile-details .job-title {
		color: #059669;
		font-weight: 500;
		margin: 0 0 0.25rem 0;
	}

	.profile-details .department {
		color: #7c3aed;
		font-size: 0.875rem;
		margin: 0;
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

	.detail-item span.detail-label {
		font-weight: 500;
		color: #374151;
	}

	.detail-item span {
		color: #6b7280;
	}

	.status-text.active {
		color: #059669;
		font-weight: 500;
	}

	.session-info {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.session-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
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
		margin: 0;
		font-size: 0.875rem;
	}

	.action-buttons {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.action-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 0.5rem;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease-in-out;
		text-decoration: none;
		font-family: inherit;
	}

	.action-btn.primary {
		background-color: #0066cc;
		color: white;
	}

	.action-btn.primary:hover:not(:disabled) {
		background-color: #0052a3;
		transform: translateY(-1px);
	}

	.action-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		transform: none;
	}

	.action-icon {
		font-size: 1.125rem;
	}

	/* Responsive design */
	@media (max-width: 768px) {
		.dashboard-container {
			padding: 1rem;
		}

		.dashboard-grid {
			grid-template-columns: 1fr;
			gap: 1.5rem;
		}

		.profile-section {
			flex-direction: column;
			text-align: center;
		}

		.action-buttons {
			justify-content: center;
		}
	}
</style>
