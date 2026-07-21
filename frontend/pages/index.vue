<template>
  <main>
    <header class="site-header">
      <div class="wordmark">
        <span class="wordmark__mark" aria-hidden="true">NO</span>
        <span>Network Operations</span>
      </div>
      <div class="environment-badge">
        <span class="environment-badge__dot" aria-hidden="true" />
        Synthetic planning environment
      </div>
    </header>

    <section class="hero" aria-labelledby="page-title">
      <div>
        <p class="eyebrow">Geodata workflow control</p>
        <h1 id="page-title">Network offer planning, with inspectable evidence.</h1>
        <p class="hero__summary">
          Evaluate candidate service corridors against demand locations through WFS feature retrieval,
          projected geometry analysis, and a standards-based WMS review link.
        </p>
      </div>
      <dl class="protocol-card" aria-label="Workflow contract">
        <div>
          <dt>Feature input</dt>
          <dd>WFS 2.0 / GeoJSON</dd>
        </div>
        <div>
          <dt>Analysis CRS</dt>
          <dd>EPSG:25830</dd>
        </div>
        <div>
          <dt>Map review</dt>
          <dd>WMS 1.3.0</dd>
        </div>
      </dl>
    </section>

    <OfferPlanner />

    <footer class="site-footer">
      <span>All network and demand features are synthetic.</span>
      <span>Protocol and calculation details remain visible for technical review.</span>
    </footer>
  </main>
</template>
