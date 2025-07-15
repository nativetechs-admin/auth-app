<script lang="ts">
	/**
	 * Projects Page Component
	 * Displays user's projects from Dataverse based on business unit
	 */

	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import ProtectedRoute from '../../lib/components/ProtectedRoute.svelte';
	import { currentUser } from '../../lib/auth/authStore';
	import { ApiService } from '../../lib/utils/api';
	import type { Project, ProjectsResponse } from '../../lib/utils/api';

	// Local state
	let projectsLoading = true;
	let projectsError = '';
	let projects: Project[] = [];

	// Reactive statements
	$: user = $currentUser;

	// Load projects on mount
	onMount(async () => {
		await loadProjects();
	});

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

	// Project functions
	async function loadProjects() {
		try {
			projectsLoading = true;
			projectsError = '';
			
			const response: ProjectsResponse = await ApiService.getUserProjects();
			projects = response.projects;
			
		} catch (err) {
			projectsError = err instanceof Error ? err.message : 'Failed to load projects';
			console.error('Error loading projects:', err);
		} finally {
			projectsLoading = false;
		}
	}

	function getProjectStatusColor(statusName: string): string {
		switch (statusName.toLowerCase()) {
			case 'active':
			case 'in progress':
				return 'status-active';
			case 'completed':
				return 'status-completed';
			case 'on hold':
				return 'status-warning';
			case 'cancelled':
			case 'inactive':
				return 'status-inactive';
			default:
				return 'status-unknown';
		}
	}

	function goBack() {
		goto('/dashboard');
	}
</script>

<svelte:head>
	<title>My Projects - SSO Application</title>
</svelte:head>

<ProtectedRoute>
	<div class="projects-container">
		<!-- Header with navigation -->
		<div class="projects-header">
			<div class="header-navigation">
				<button class="back-btn" on:click={goBack}>
					<span class="back-icon">←</span>
					Back to Dashboard
				</button>
			</div>
			<div class="header-content">
				<h1>My Projects</h1>
				<p>Projects from your business unit in Microsoft Dataverse</p>
			</div>
			<div class="header-actions">
				<button class="refresh-btn" on:click={loadProjects} disabled={projectsLoading}>
					<span class="refresh-icon">🔄</span>
					{projectsLoading ? 'Loading...' : 'Refresh'}
				</button>
			</div>
		</div>

		<!-- Projects Content -->
		<div class="projects-content">
			{#if projectsLoading}
				<div class="loading-state">
					<div class="spinner"></div>
					<h3>Loading Your Projects</h3>
					<p>Fetching projects from Microsoft Dataverse...</p>
				</div>
			{:else if projectsError}
				<div class="error-state">
					<span class="error-icon">⚠️</span>
					<h3>Failed to Load Projects</h3>
					<p>{projectsError}</p>
					<button class="retry-btn" on:click={loadProjects}>
						Try Again
					</button>
				</div>
			{:else if projects.length === 0}
				<div class="empty-state">
					<span class="empty-icon">📂</span>
					<h3>No Projects Found</h3>
					<p>You don't have access to any projects in your business unit.</p>
					<p class="empty-subtitle">Contact your administrator if you believe this is incorrect.</p>
				</div>
			{:else}
				<div class="projects-summary">
					<div class="summary-card">
						<h3>Projects Overview</h3>
						<div class="summary-stats">
							<div class="stat-item">
								<span class="stat-number">{projects.length}</span>
								<span class="stat-label">Total Projects</span>
							</div>
							<div class="stat-item">
								<span class="stat-number">{projects.filter(p => p.status_name.toLowerCase().includes('active') || p.status_name.toLowerCase().includes('progress')).length}</span>
								<span class="stat-label">Active</span>
							</div>
							<div class="stat-item">
								<span class="stat-number">{projects.filter(p => p.status_name.toLowerCase().includes('completed')).length}</span>
								<span class="stat-label">Completed</span>
							</div>
						</div>
					</div>
				</div>

				<div class="projects-grid">
					{#each projects as project}
						<div class="project-card">
							<div class="project-header">
								<h4 class="project-name">{project.name || 'Untitled Project'}</h4>
								<span class="status-badge {getProjectStatusColor(project.status_name)}">
									{project.status_name}
								</span>
							</div>
							{#if project.description}
								<p class="project-description">{project.description}</p>
							{/if}
							<div class="project-meta">
								<div class="meta-section">
									<h5>Project Details</h5>
									{#if project.statuscode_text}
										<div class="meta-item">
											<span class="meta-label">Status:</span>
											<span class="meta-value">{project.statuscode_text}</span>
										</div>
									{/if}
									{#if project.msdyn_subject}
										<div class="meta-item">
											<span class="meta-label">Subject:</span>
											<span class="meta-value">{project.msdyn_subject}</span>
										</div>
									{/if}
								</div>
								<div class="meta-section">
									<h5>Timeline</h5>
									{#if project.msdyn_scheduledstart}
										<div class="meta-item">
											<span class="meta-label">Scheduled Start:</span>
											<span class="meta-value">{formatDate(project.msdyn_scheduledstart)}</span>
										</div>
									{/if}
									<div class="meta-item">
										<span class="meta-label">Created:</span>
										<span class="meta-value">{formatDate(project.created_on)}</span>
									</div>
									<div class="meta-item">
										<span class="meta-label">Modified:</span>
										<span class="meta-value">{formatDate(project.modified_on)}</span>
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</ProtectedRoute>

<style>
	.projects-container {
		max-width: 1400px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
	}

	.projects-header {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		margin-bottom: 2rem;
		padding-bottom: 2rem;
		border-bottom: 1px solid #e5e7eb;
	}

	.header-navigation {
		display: flex;
		align-items: center;
	}

	.back-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: #f3f4f6;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		color: #374151;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s ease-in-out;
		font-family: inherit;
	}

	.back-btn:hover {
		background: #e5e7eb;
		color: #111827;
	}

	.back-icon {
		font-size: 1rem;
	}

	.header-content {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.header-content h1 {
		font-size: 2.5rem;
		font-weight: 700;
		color: #111827;
		margin: 0;
	}

	.header-content p {
		color: #6b7280;
		font-size: 1.125rem;
		margin: 0;
	}

	.header-actions {
		display: flex;
		justify-content: flex-end;
	}

	.refresh-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		background: #0066cc;
		color: white;
		border: none;
		border-radius: 0.5rem;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease-in-out;
		font-family: inherit;
	}

	.refresh-btn:hover:not(:disabled) {
		background: #0052a3;
		transform: translateY(-1px);
	}

	.refresh-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		transform: none;
	}

	.refresh-icon {
		font-size: 1rem;
	}

	.projects-content {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.loading-state,
	.error-state,
	.empty-state {
		text-align: center;
		padding: 4rem 2rem;
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
	}

	.spinner {
		width: 3rem;
		height: 3rem;
		border: 3px solid #e5e7eb;
		border-top: 3px solid #0066cc;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 2rem;
	}

	.loading-state h3,
	.error-state h3,
	.empty-state h3 {
		font-size: 1.5rem;
		font-weight: 600;
		color: #111827;
		margin: 0 0 1rem 0;
	}

	.loading-state p,
	.error-state p,
	.empty-state p {
		color: #6b7280;
		margin: 0;
		line-height: 1.5;
	}

	.empty-subtitle {
		font-size: 0.875rem;
		color: #9ca3af !important;
		margin-top: 0.5rem !important;
	}

	.error-icon,
	.empty-icon {
		font-size: 3rem;
		margin-bottom: 1rem;
		display: block;
	}

	.retry-btn {
		background: #dc2626;
		color: white;
		border: none;
		border-radius: 0.375rem;
		padding: 0.75rem 1.5rem;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s ease-in-out;
		margin-top: 1.5rem;
	}

	.retry-btn:hover {
		background: #b91c1c;
	}

	.projects-summary {
		margin-bottom: 2rem;
	}

	.summary-card {
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
		padding: 2rem;
	}

	.summary-card h3 {
		font-size: 1.5rem;
		font-weight: 600;
		color: #111827;
		margin: 0 0 1.5rem 0;
	}

	.summary-stats {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 2rem;
	}

	.stat-item {
		text-align: center;
	}

	.stat-number {
		display: block;
		font-size: 2.5rem;
		font-weight: 700;
		color: #0066cc;
		margin-bottom: 0.5rem;
	}

	.stat-label {
		display: block;
		font-size: 0.875rem;
		font-weight: 500;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.projects-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
		gap: 2rem;
	}

	.project-card {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 0.75rem;
		padding: 2rem;
		transition: all 0.2s ease-in-out;
		box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
	}

	.project-card:hover {
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
		transform: translateY(-2px);
	}

	.project-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1.5rem;
		gap: 1rem;
	}

	.project-name {
		font-size: 1.25rem;
		font-weight: 600;
		color: #111827;
		margin: 0;
		flex: 1;
		line-height: 1.3;
	}

	.status-badge {
		padding: 0.375rem 0.875rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		flex-shrink: 0;
	}

	.status-active {
		background-color: #d1fae5;
		color: #065f46;
	}

	.status-completed {
		background-color: #dbeafe;
		color: #1e40af;
	}

	.status-warning {
		background-color: #fef3c7;
		color: #92400e;
	}

	.status-inactive {
		background-color: #fee2e2;
		color: #991b1b;
	}

	.status-unknown {
		background-color: #f3f4f6;
		color: #374151;
	}

	.project-description {
		color: #6b7280;
		margin: 0 0 1.5rem 0;
		line-height: 1.6;
		font-size: 0.875rem;
	}

	.project-meta {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
	}

	.meta-section {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.meta-section h5 {
		font-size: 0.875rem;
		font-weight: 600;
		color: #374151;
		margin: 0;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid #f3f4f6;
	}

	.meta-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.875rem;
		gap: 1rem;
	}

	.meta-label {
		color: #6b7280;
		font-weight: 500;
		flex-shrink: 0;
	}

	.meta-value {
		color: #111827;
		text-align: right;
		word-break: break-all;
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		font-size: 0.8rem;
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
	@media (max-width: 768px) {
		.projects-container {
			padding: 1rem;
		}

		.projects-header {
			gap: 1rem;
		}

		.header-content h1 {
			font-size: 2rem;
		}

		.header-actions {
			justify-content: flex-start;
		}

		.projects-grid {
			grid-template-columns: 1fr;
		}

		.project-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.project-meta {
			grid-template-columns: 1fr;
			gap: 1.5rem;
		}

		.summary-stats {
			grid-template-columns: repeat(3, 1fr);
			gap: 1rem;
		}

		.stat-number {
			font-size: 2rem;
		}
	}
</style>
