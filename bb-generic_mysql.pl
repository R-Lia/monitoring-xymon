#!/usr/bin/env perl 

#### Meta information
# Original author : ZeWaren
# Modified by : Aurelia Bordes (sys.vision)

use strict;
use warnings;

use DBI;
use DBD::mysql;
use Sys::Hostname;
use Getopt::Std;

use constant DBI_URN => 'DBI:mysql:performance_schema';
use constant XYMON_WWW_ROOT => '';

my ($DBI_USERNAME, $DBI_PASSWORD);

#### Functions
sub get_graph_html {
        my ($host, $service) = @_;
        '<table summary="'.$service.' Graph"><tr><td><A HREF="'.XYMON_WWW_ROOT.'/xymon-cgi/showgraph.sh?host='.$host.'&amp;service='.$service.'&amp;graph_width=576&amp;graph_height=120&amp;first=1&amp;count=1&amp;disp='.$host.'&amp;action=menu"><IMG BORDER=0 SRC="'.XYMON_WWW_ROOT.'/xymon-cgi/showgraph.sh?host='.$host.'&amp;service='.$service.'&amp;graph_width=576&amp;graph_height=120&amp;first=1&amp;count=1&amp;disp='.$host.'&amp;graph=hourly&amp;action=view" ALT="xymongraph '.$service.'"></A></td></tr></table>';
}

sub doc {
	print "Usage: [-h] -u [username] -p [password]

        Required parameters:

        -u [username]	username of mysql server
	
	-p [password] 	password corresponding to the username

        Optional parameters:

        -h			Display this help message and exit.
"

}

#### Process command line options
our($opt_h, $opt_u,$opt_p);
getopts("hu:p:");	# Command line options allowed and set $opt_* as a side effect.

if (defined $opt_h) {
  	doc;
	exit;
} elsif (defined $opt_u and defined $opt_p){
	$DBI_USERNAME=$opt_u;
	$DBI_PASSWORD=$opt_p;
} else {
	doc;
	exit;
}

my $dbh = DBI->connect(DBI_URN, $DBI_USERNAME, $DBI_PASSWORD) or die($DBI::errstr);

my $sth = $dbh->prepare("SELECT * FROM performance_schema.global_status");
$sth->execute( ) or die($DBI::errstr);
my $values = {};
while ( my @row = $sth->fetchrow_array ) {
    $values->{$row[0]} = $row[1];
}

$sth = $dbh->prepare("SELECT VARIABLE_NAME, VARIABLE_VALUE FROM performance_schema.global_variables WHERE VARIABLE_NAME IN ('MAX_CONNECTIONS', 'QUERY_CACHE_SIZE', 'TABLE_OPEN_CACHE')");
$sth->execute( ) or die($DBI::errstr);

while ( my @row = $sth->fetchrow_array ) {
    $values->{$row[0]} = $row[1];
}

$sth = $dbh->prepare("SELECT EVENT_NAME, COUNT_STAR FROM performance_schema.events_statements_summary_global_by_event_name WHERE EVENT_NAME in ('statement/sql/select','statement/sql/update','statement/sql/delete', 'statement/sql/insert','statement/sql/insert_select','statement/sql/load','statement/sql/replace','statement/sql/delete_multi','statement/sql/update_multi','statement/sql/replace_select','statement/sql/call_procedure')");
$sth->execute( ) or die($DBI::errstr);
while ( my @row = $sth->fetchrow_array ) {
    $values->{$row[0]} = $row[1];
}

my $trends = "
[mysql_activity.rrd]
DS:sel:DERIVE:600:0:U ".$values->{'statement/sql/select'}."
DS:ins:DERIVE:600:0:U ".$values->{'statement/sql/insert'}."
DS:upd:DERIVE:600:0:U ".$values->{'statement/sql/update'}."
DS:rep:DERIVE:600:0:U ".$values->{'statement/sql/replace'}."
DS:del:DERIVE:600:0:U ".$values->{'statement/sql/delete'}."
DS:cal:DERIVE:600:0:U ".$values->{'statement/sql/call_procedure'}."
[mysql_connections.rrd]
DS:max_connections:GAUGE:600:0:U ".$values->{max_connections}."
DS:max_used:GAUGE:600:0:U ".$values->{Max_used_connections}."
DS:aborted_clients:DERIVE:600:0:U ".$values->{Aborted_clients}."
DS:aborted_connects:DERIVE:600:0:U ".$values->{Aborted_connects}."
DS:threads_connected:GAUGE:600:0:U ".$values->{Threads_connected}."
DS:threads_running:GAUGE:600:0:U ".$values->{Threads_running}."
DS:new_connections:DERIVE:600:0:U ".$values->{Connections}."
[mysql_command_counters.rrd]
DS:questions:DERIVE:600:0:U ".$values->{Questions}."
DS:select:DERIVE:600:0:U ".$values->{'statement/sql/select'}."
DS:delete:DERIVE:600:0:U ".$values->{'statement/sql/delete'}."
DS:insert:DERIVE:600:0:U ".$values->{'statement/sql/insert'}."
DS:update:DERIVE:600:0:U ".$values->{'statement/sql/update'}."
DS:replace:DERIVE:600:0:U ".$values->{'statement/sql/replace'}."
DS:load:DERIVE:600:0:U ".$values->{'statement/sql/load'}."
DS:delete_multi:DERIVE:600:0:U ".$values->{'statement/sql/delete_multi'}."
DS:insert_select:DERIVE:600:0:U ".$values->{'statement/sql/insert_select'}."
DS:update_multi:DERIVE:600:0:U ".$values->{'statement/sql/update_multi'}."
DS:replace_select:DERIVE:600:0:U ".$values->{'statement/sql/replace_select'}."
[mysql_files_and_tables.rrd]
DS:table_open_cache:GAUGE:600:0:U ".$values->{table_open_cache}."
DS:open_tables:GAUGE:600:0:U ".$values->{Open_tables}."
DS:opened_files:DERIVE:600:0:U ".$values->{Opened_files}."
DS:opened_tables:DERIVE:600:0:U ".$values->{Opened_tables}."
[mysql_handlers.rrd]
DS:write:DERIVE:600:0:U ".$values->{Handler_write}."
DS:update:DERIVE:600:0:U ".$values->{Handler_update}."
DS:delete:DERIVE:600:0:U ".$values->{Handler_delete}."
DS:read_first:DERIVE:600:0:U ".$values->{Handler_read_first}."
DS:read_key:DERIVE:600:0:U ".$values->{Handler_read_key}."
DS:read_next:DERIVE:600:0:U ".$values->{Handler_read_next}."
DS:read_prev:DERIVE:600:0:U ".$values->{Handler_read_prev}."
DS:read_rnd:DERIVE:600:0:U ".$values->{Handler_read_rnd}."
DS:read_rnd_next:DERIVE:600:0:U ".$values->{Handler_read_rnd_next}."
[mysql_query_cache.rrd]
DS:queries_in_cache:DERIVE:600:0:U ".$values->{Qcache_queries_in_cache}."
DS:hits:DERIVE:600:0:U ".$values->{Qcache_hits}."
DS:inserts:DERIVE:600:0:U ".$values->{Qcache_inserts}."
DS:not_cached:DERIVE:600:0:U ".$values->{Qcache_not_cached}."
DS:lowmem_prunes:DERIVE:600:0:U ".$values->{Qcache_lowmem_prunes}."
[mysql_prepared_statements.rrd]
DS:stmt_count:GAUGE:600:0:U ".$values->{Prepared_stmt_count}."
[mysql_select_types.rrd]
DS:full_join:DERIVE:600:0:U ".$values->{Select_full_join}."
DS:full_range_join:DERIVE:600:0:U ".$values->{Select_full_range_join}."
DS:range:DERIVE:600:0:U ".$values->{Select_range}."
DS:range_check:DERIVE:600:0:U ".$values->{Select_range_check}."
DS:scan:DERIVE:600:0:U ".$values->{Select_scan}."
[mysql_sorts.rrd]
DS:sort_rows:DERIVE:600:0:U ".$values->{Sort_rows}."
DS:sort_range:DERIVE:600:0:U ".$values->{Sort_range}."
DS:sort_merge_passes:DERIVE:600:0:U ".$values->{Sort_merge_passes}."
DS:sort_scan:DERIVE:600:0:U ".$values->{Sort_scan}."
[mysql_table_locks.rrd]
DS:immediate:DERIVE:600:0:U ".$values->{Table_locks_immediate}."
DS:waited:DERIVE:600:0:U ".$values->{Table_locks_waited}."
[mysql_temp_objects.rrd]
DS:tables:DERIVE:600:0:U ".$values->{Created_tmp_tables}."
DS:tmp_disk_tables:DERIVE:600:0:U ".$values->{Created_tmp_disk_tables}."
DS:tmp_files:DERIVE:600:0:U ".$values->{Created_tmp_files}."
[mysql_transaction_handlers.rrd]
DS:commit:DERIVE:600:0:U ".$values->{Handler_commit}."
DS:rollback:DERIVE:600:0:U ".$values->{Handler_rollback}."
DS:savepoint:DERIVE:600:0:U ".$values->{Handler_savepoint}."
DS:savepoint_rollback:DERIVE:600:0:U ".$values->{Handler_savepoint_rollback}."
";

my $host = $ENV{MACHINEDOTS};
my $report_date = `/bin/date`;
my $color = 'clear';
my $service = 'mysql';

my $data = "
<h2>Status</h2>
Server : localhost

No status checked

<h2>Counters</h2>
".get_graph_html($host, 'mysql_activity')."
".get_graph_html($host, 'mysql_command_counters')."
".get_graph_html($host, 'mysql_connections')."
".get_graph_html($host, 'mysql_files_and_tables')."
".get_graph_html($host, 'mysql_handlers')."
".get_graph_html($host, 'mysql_query_cache')."
".get_graph_html($host, 'mysql_select_types')."
".get_graph_html($host, 'mysql_sorts')."
".get_graph_html($host, 'mysql_table_locks')."
".get_graph_html($host, 'mysql_temp_objects')."
".get_graph_html($host, 'mysql_transaction_handlers')."
".get_graph_html($host, 'mysql_prepared_statements')."

";

#DEBUG
#print($data);
#print($trends);

system( ("$ENV{BB}", "$ENV{BBDISP}", "status $host.$service $color $report_date$data\n") );
system( "$ENV{BB} $ENV{BBDISP} 'data $host.trends $trends'\n");
