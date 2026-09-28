import { useLayoutEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import data from '../content/profile.json';

const { profile, education, research } = data;
const routes = { top: 'Home', work: 'Work', about: 'About', research: 'Research', now: 'Now' };
const resumeUrl = 'assets/Kshitiz-Neupane-Resume.pdf';

function routeFromLocation() {
  const hash = window.location.hash.slice(1);
  if (Object.hasOwn(routes, hash)) return hash;
  if (hash.startsWith('project/')) {
    const id = hash.slice('project/'.length);
    if (data.projects.some((project) => project.id === id)) return hash;
  }
  return 'top';
}

function Arrow() {
  return <span aria-hidden="true">↗</span>;
}

function ProjectImage({ project, eager = false }) {
  return <figure className="project-figure"><a href={project.image} target="_blank" rel="noreferrer" aria-label={`Open full-size figure for ${project.name}`}><img src={project.image} alt={project.image_alt} loading={eager ? 'eager' : 'lazy'} width="1000" height="650" /><span className="figure-expand" aria-hidden="true">↗</span></a><figcaption>{project.caption}</figcaption></figure>;
}

function Home({ navigate }) {
  return <section className="home-simple wrap" data-page="top" aria-labelledby="intro-title">
    <p className="eyebrow">{profile.discipline}</p>
    <div className="home-profile"><div><h1 id="intro-title">{profile.name}</h1><p className="home-motto">{profile.bio[0]}</p><p className="home-intro">{profile.intro}</p><div className="home-links"><a href="#work" onClick={e => navigate(e, 'work')}>Projects <Arrow /></a><a href="#research" onClick={e => navigate(e, 'research')}>Research <Arrow /></a><a href={`mailto:${profile.email}`}>Get in touch <Arrow /></a></div></div><img className="home-avatar" src="assets/avatar_sketch_under_1mb.jpg" alt="Pencil sketch portrait of Kshitiz Neupane" width="1254" height="1254" /></div>
    <div className="home-current"><p className="eyebrow">Currently working on</p><p>agriculture-ai · WMSV · solver-verifier-research</p><a className="text-link" href="#now" onClick={e => navigate(e, 'now')}>A little about each <Arrow /></a></div>
  </section>;
}

function Project({ project, index }) {
  return <article className="project" id={`project-${project.id}`} aria-labelledby={`title-${project.id}`}><div className="project-visual"><ProjectImage project={project} /></div><div className="project-info"><p className="project-category">{String(index + 1).padStart(2, '0')} / {project.category}</p><h2 id={`title-${project.id}`}>{project.name}</h2><p className="project-description">{project.description}</p><ul className="tags" aria-label="Technologies">{project.stack.slice(0, 3).map(tag => <li key={tag}>{tag}</li>)}</ul><div className="project-actions"><a className="project-link" href={`#project/${project.id}`}>View project <Arrow /></a>{project.url && <a className="project-link secondary" href={project.url}>Repository <Arrow /></a>}</div></div></article>;
}

function ProjectDetail({ project }) {
  const projectIndex = data.projects.findIndex((item) => item.id === project.id);
  const nextProject = data.projects[(projectIndex + 1) % data.projects.length];
  const visuals = [
    { image: project.image, alt: project.image_alt, caption: project.caption },
    ...(project.gallery || []),
  ];

  return <article className="project-page wrap" data-page={`project-${project.id}`} aria-labelledby="project-page-title">
    <a className="back-link" href="#work">← Back to work</a>
    <header className="project-page-header"><div><p className="project-category">{project.category}</p><h1 className="page-title" id="project-page-title">{project.name}</h1><p className="project-page-question">{project.question}</p></div><div className="project-page-summary"><p>{project.description}</p>{project.url && <a className="project-link" href={project.url}>View repository <Arrow /></a>}</div></header>
    <figure className="project-page-lead"><a href={project.image} target="_blank" rel="noreferrer"><img src={project.image} alt={project.image_alt} width="1400" height="900" /></a><figcaption>{project.caption}</figcaption></figure>
    <div className="project-page-content"><section aria-labelledby="about-project"><p className="eyebrow">About the project</p><h2 id="about-project">What it is</h2>{project.details.map(paragraph => <p key={paragraph}>{paragraph}</p>)}</section><aside><p className="eyebrow">What it includes</p><ul>{project.highlights.map(item => <li key={item}>{item}</li>)}</ul><p className="eyebrow tools-label">Tools</p><ul className="tags" aria-label="Technologies">{project.stack.map(tag => <li key={tag}>{tag}</li>)}</ul>{project.result && <p className="detail-result">{project.result}</p>}</aside></div>
    {visuals.length > 1 && <section className="project-page-gallery" aria-labelledby="gallery-title"><div className="gallery-heading"><p className="eyebrow">Project visuals</p><h2 id="gallery-title">Results and interface</h2><p>Open any image to see it at full size.</p></div><div className="detail-gallery">{visuals.map((visual, index) => <figure key={visual.image} className={index === 0 ? 'wide' : ''}><a href={visual.image} target="_blank" rel="noreferrer" aria-label={`Open full-size image: ${visual.caption}`}><img src={visual.image} alt={visual.alt} loading={index === 0 ? 'eager' : 'lazy'} width="1000" height="650" /></a><figcaption>{visual.caption}</figcaption></figure>)}</div></section>}
    <nav className="project-next" aria-label="Project navigation"><span>Next project</span><a href={`#project/${nextProject.id}`}>{nextProject.name} <Arrow /></a></nav>
  </article>;
}

function Work() {
  const [filter, setFilter] = useState('Machine learning');
  const filters = ['Machine learning', 'Data science', 'Software'];
  const visible = data.projects.filter(p => (filter === 'Machine learning' && ['ML reliability', 'Statistical learning'].includes(p.group)) || (filter === 'Data science' && ['Data science', 'Statistical learning'].includes(p.group)) || (filter === 'Software' && p.group === 'Software'));
  return <section className="work-section wrap" data-page="work" aria-labelledby="work-title"><div className="section-heading"><div><p className="eyebrow">01 / Selected work</p><h1 className="page-title" id="work-title">Projects</h1></div><p>A few things I’ve built and learned along the way.</p></div><div className="filters" aria-label="Filter projects">{filters.map(item => <button key={item} aria-pressed={filter === item} onClick={() => setFilter(item)}>{item}</button>)}<span aria-live="polite">{visible.length} projects</span></div><div className="project-list">{visible.map(project => <Project key={project.id} project={project} index={data.projects.indexOf(project)} />)}</div><section className="work-experience" aria-labelledby="experience-title"><h2 className="eyebrow" id="experience-title">Experience</h2>{data.experience.map(item => <article className="experience-item" key={item.role}><h3>{item.role}</h3><p>{item.organization} · {item.dates}</p><p>{item.summary}</p></article>)}</section></section>;
}

function About() {
  return (
    <section className="about-section wrap" data-page="about" aria-labelledby="about-title">
      <div className="section-side"><p className="eyebrow">02 / A little about me</p><h1 className="page-title" id="about-title">About</h1><figure className="about-portrait"><img src="assets/avatar_sketch_under_1mb.jpg" alt="Pencil sketch portrait of Kshitiz Neupane" width="1254" height="1254" /></figure></div>
      <div className="about-content">
        <div className="bio"><p>{profile.about}</p></div>
        <div className="skill-list">{data.skills.map(skill => <div key={skill.label}><p className="eyebrow">{skill.label}</p><p>{skill.items}</p></div>)}</div><section className="education" aria-labelledby="education-title">
          <p className="eyebrow">Education</p><h2 id="education-title">{education.institution}</h2><p>{education.degree}</p>
          <p className="education-detail">{education.graduation} <span aria-hidden="true">·</span> GPA {education.gpa}</p>
          <p className="coursework"><strong>Coursework</strong><br />{education.coursework}</p>
        </section>
      </div>
    </section>
  );
}

function Research() {
  const paper = research.publication;
  return <section className="research-section wrap" data-page="research" aria-labelledby="research-title">
    <div className="research-heading"><p className="eyebrow">Research</p><h1 className="page-title" id="research-title">What I’m studying</h1></div>
    <div className="research-entries"><article className="research-entry"><p className="eyebrow">{paper.status}</p><h2>{paper.title}</h2><p className="paper-subtitle">{paper.subtitle}</p><p className="paper-authors">{paper.authors}</p><p>{paper.description}</p><div className="paper-links"><a href={paper.url}>Read the paper <Arrow /></a><a href={paper.scholar_url}>Google Scholar <Arrow /></a></div></article>
    <article className="research-entry"><p className="eyebrow">{research.current.status}</p><h2>{research.current.title}</h2><p>{research.current.description}</p></article>
    <div className="research-interest"><p className="eyebrow">Also interested in</p><h2>{research.title}</h2><p>{research.description}</p></div></div>
  </section>;
}

function Now() {
  const updated = new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${data.updated}T00:00:00Z`));
  return (
    <section className="now-band" data-page="now" aria-labelledby="now-title">
      <div className="wrap now-layout">
        <div><p className="eyebrow light">In progress</p><h1 className="page-title" id="now-title">Ongoing projects</h1><p className="updated">Updated <time dateTime={data.updated}>{updated}</time></p></div>
        <div className="now-items">{data.now.map((item) => (
          <article className="now-item" key={item.title}><p className="status">{item.label}</p><h2>{item.url ? <a href={item.url}>{item.title} <Arrow /></a> : item.title}</h2><p>{item.description}</p></article>
        ))}</div>
      </div>
    </section>
  );
}

const pages = { top: Home, work: Work, about: About, research: Research, now: Now };

function App() {
  const [route, setRoute] = useState(routeFromLocation);
  const main = useRef(null);
  const firstRender = useRef(true);

  useLayoutEffect(() => {
    function syncRoute() {
      if (window.location.hash !== '#main') setRoute(routeFromLocation());
    }
    window.addEventListener('hashchange', syncRoute);
    window.addEventListener('popstate', syncRoute);
    return () => {
      window.removeEventListener('hashchange', syncRoute);
      window.removeEventListener('popstate', syncRoute);
    };
  }, []);

  useLayoutEffect(() => {
    const project = route.startsWith('project/') ? data.projects.find((item) => item.id === route.slice('project/'.length)) : null;
    document.title = route === 'top' ? `${profile.name} — Portfolio` : `${project?.name || routes[route]} — ${profile.name}`;
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    if (firstRender.current) {
      firstRender.current = false;
    } else {
      const heading = main.current.querySelector('h1');
      heading.tabIndex = -1;
      heading.focus({ preventScroll: true });
    }
  }, [route]);

  function navigate(event, nextRoute) {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (window.location.hash !== `#${nextRoute}`) window.history.pushState(null, '', `#${nextRoute}`);
    setRoute(nextRoute);
  }

  // Only this component is mounted. Switching the key removes the previous page's DOM.
  const project = route.startsWith('project/') ? data.projects.find((item) => item.id === route.slice('project/'.length)) : null;
  const Page = project ? ProjectDetail : pages[route];
  return (
    <>
      <a className="skip-link" href="#main" onClick={(event) => { event.preventDefault(); main.current.focus(); }}>Skip to content</a>
      <header className="site-header wrap">
        <a className="mark" href="#top" onClick={(event) => navigate(event, 'top')} aria-label={`${profile.name}, home`}>{profile.initials}<span aria-hidden="true">.</span></a>
        <nav aria-label="Main navigation">{Object.entries(routes).filter(([key]) => key !== 'top').map(([key, label]) => (
          <a key={key} href={`#${key}`} onClick={(event) => navigate(event, key)} aria-current={route === key || (key === 'work' && project) ? 'page' : undefined}>{label}</a>
        ))}</nav>
        <a className="header-resume" href={resumeUrl} download>Résumé <span aria-hidden="true">↓</span></a>
      </header>
      <main id="main" ref={main} tabIndex={-1}><Page key={route} navigate={navigate} project={project} /></main>
      {route === 'top' && <footer className="site-footer wrap"><p>© {data.updated.slice(0, 4)} {profile.name}</p><p>{profile.location}</p><div className="social-links"><a href={profile.github}>GitHub <Arrow /></a><a href={profile.linkedin}>LinkedIn <Arrow /></a><a href={`mailto:${profile.email}`}>Email <Arrow /></a></div></footer>}
    </>
  );
}

createRoot(document.getElementById('app')).render(<App />);
