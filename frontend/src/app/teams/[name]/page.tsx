import TeamDetailClient from './client';

const TEAMS = [
  'Algeria','Argentina','Australia','Austria','Belgium','Bosnia and Herzegovina','Brazil',
  'Canada','Cape Verde','Colombia','Croatia','Curaçao','Czech Republic','Czechia',
  'DR Congo','Ecuador','Egypt','England','France','Germany','Ghana','Haiti',
  'Iran','Iraq','Ivory Coast','Japan','Jordan','Mexico','Morocco','Netherlands',
  'New Zealand','Norway','Panama','Paraguay','Portugal','Qatar','Saudi Arabia',
  'Scotland','Senegal','South Africa','South Korea','Spain','Sweden','Switzerland',
  'Tunisia','Turkey','United States','Uruguay','Uzbekistan',
];

export async function generateStaticParams() {
  return TEAMS.map(name => ({ name }));
}

export default function TeamDetailPage() {
  return <TeamDetailClient />;
}
