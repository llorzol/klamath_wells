#!/usr/bin/perl -w 

=head1 NAME

Prepare Groundwater Measurements Script: prepare_gwlevels_file.pl

=head1 DESCRIPTION

 Script prepares the file called collection.txt by loading site records from
  the USGS, OWRD, and CDWR sources. The script will insert new records, update
  existing records and delete orphaned records (an orphaned record is a site
  that exists in the collection file, but there is no longer a record of it
  in any the three source databases).

=head1 SYNOPSIS

prepare_gwlevels_file.pl { I<args> } 

=head1 ARGUMENTS

B<--usgs>    Retrieve groundwater measurements from NWIS

B<--owrd>    Retrieve groundwater measurements from OWRD

B<--cdwr>    Retrieve groundwater measurements from CDWR

B<--all>     Retrieve groundwater measurements from NWIS, OWRD,  and CDWR

B<--report>  Builds a file of groundwater measurements for each site

=over 1

=back

=head1 EXAMPLES

=over 2

=back

=head1 COPYRIGHT

Copyright (c) 2014 Oregon Water Science Center
 
 Permission is hereby granted, free of charge, to any person obtaining a
 copy of this software and associated documentation files (the "Software"),
 to deal in the Software without restriction, including without limitation
 the rights to use, copy, modify, merge, publish, distribute, sublicense,
 and/or sell copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included
 in all copies or substantial portions of the Software.

=head1 DISCLAIMER

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 DEALINGS IN THE SOFTWARE.

=cut

use strict;

use FindBin;
use Getopt::Long;
use Pod::Usage;

use Date::Calc qw(Date_to_Time Date_to_Days Month_to_Text Today_and_Now Date_to_Text_Long Timezone Add_Delta_Days Add_Delta_DHMS);
use DateTime;
use Time::Zone;
use Time::Local;

use IO::File;
use File::Path;
use File::Copy;
use File::Spec::Functions;

use Log::Log4perl qw(get_logger :levels);

# Track the time for the completion of the data
#
use Time::HiRes qw(gettimeofday tv_interval);

# Version
#
my $task         = $FindBin::Script;
my $version      = "version 1.21";
my $version_date = "14October2014"; 

#######################################################
#
#            Check all of the users arguments.
#
#######################################################
my $screen_logger               = undef;
my $file_logger                 = undef;

my $usgs_file                   = undef;
my $owrd_file                   = undef;
my $cdwr_file                   = undef;
my $all                         = undef;

my $force                       = undef;
my $quiet                       = undef;
my $help                        = undef;
my $debug                       = undef;
my $logging                     = undef;
my $file                        = undef;
my $report                      = undef;

my $program_args                = "";

my @lev_columns                 = (
                                   'site_id',
                                   'agency_cd',
                                   'site_no',
                                   'coop_site_no',
                                   'cdwr_id',
                                   'lev_va',
                                   'lev_acy_cd',
                                   'lev_dtm',
                                   'lev_dt',
                                   'lev_tm',
                                   'lev_tz_cd',
                                   'lev_dt_acy_cd',
                                   'lev_str_dt',
                                   'lev_status_cd',
                                   'lev_meth_cd',
                                   'lev_agency_cd',
                                   'lev_src_cd',
                                   'lev_rmk_tx',
                                  );

my @lev_formats                 = (
                                   '15s',
                                   '5s',
                                   '15s',
                                   '10s',
                                   '10s',
                                   '10s',
                                   '1s',
                                   '20s',
                                   '20s',
                                   '10s',
                                   '1s',
                                   '1s',
                                   '20s',
                                   '1s',
                                   '1s',
                                   '20s',
                                   '1s',
                                   '100s',
                                  );

# Set screen logger
#
$screen_logger = set_screen_logger();

# Check the user arguments
#
&check_options();

# Call the init function
#
&init();

# Set the log file
#
if(defined($logging))
  {
   &set_file_logger();
  }

# Messages to screen and log file
#
my ($year, $month, $day, $hour, $min, $sec) = Today_and_Now();
my $date_string                             = Date_to_Text_Long($year, $month, $day);

# Log arguments
#
$screen_logger->info("############################################################################");
$screen_logger->info(" Start: $date_string                          ");
$screen_logger->info(" Prog: $FindBin::Script");
$screen_logger->info(" Args: $program_args");
$screen_logger->info("----------------------------------------------------------------------------\n");

# Read present collection file to obtain sites
#
my $collection_file = "collection.txt";

# Build column names
# 
my @WANTED_COLUMNS = (
                      'site_id',
                      'agency_cd',
                      'site_no',
                      'coop_site_no',
                      'cdwr_id',
                      'station_nm'
                     );
   
my @WANTED_FORMATS = (
                      '15s',
                      '15s',
                      '15s',
                      '10s',
                      '10s',
                      '100s'
                     );
   
# Read list of sites
# 
my %Site_Hash = ();
my %Owrd_Hash = ();
my %Cdwr_Hash = ();

if(-e $collection_file)
  { 
   my $fh = IO::File->new($collection_file, "r");
   if(defined $fh)
     {
      my @file_lines = <$fh>;
      my $file_line  = "";
      while (scalar(@file_lines) > 0)
        {
         $file_line  =  shift @file_lines;
         $file_line     =~ s/\r?\n//;
         last if($file_line !~ m/^\#/);
        }
                            
      # Read data
      # 
      my @INPUT_COLUMNS = ();
        
      my $Field_Separator = "\t";
        
      # Parse columns
      #  
      $Field_Separator = &check_columns ($file_line, \@WANTED_COLUMNS, $collection_file);
         
      # Parse columns
      #  
      @INPUT_COLUMNS = split(/$Field_Separator/, $file_line);
         
      # Omit format line
      #  
      $file_line  =  shift @file_lines;

      # Parse for sites
      #  
      my %row = ();
      while(scalar(@file_lines) > 0)
        {
         my $file_line = shift @file_lines;
         $file_line    =~ s/\r?\n//;
         my %row       = ();
         @row{@INPUT_COLUMNS} = split("\t", $file_line);
              
         my $site_id      = $row{'site_id'};

         my $agency_cd    = "";
         $agency_cd       = $row{'agency_cd'}    if(defined($row{'agency_cd'}));
         my $site_no      = "";
         $site_no         = $row{'site_no'}      if(defined($row{'site_no'}));
         my $coop_site_no = "";
         $coop_site_no    = $row{'coop_site_no'} if(defined($row{'coop_site_no'}));
         if(length($coop_site_no) > 0)
           {
             my ($county, $log_id) = split(/\s+/, $coop_site_no);
             $coop_site_no = sprintf("%4s%6s", $county, $log_id);
           }
         my $cdwr_id      = "";
         $cdwr_id         = $row{'cdwr_id'}      if(defined($row{'cdwr_id'}));
         #print "Site agency_cd $agency_cd site_no $site_no coop_site_no $coop_site_no\n";

         # Loop through columns
         #
         foreach my $column (@INPUT_COLUMNS)
           {
            $row{$column} = "" if(not defined($row{$column}));
            $Site_Hash{$site_id}{$column} = $row{$column};
           }

         if(length($coop_site_no) > 0)
           {
            $Owrd_Hash{$coop_site_no}{'site_id'}   = $site_id   if(length($coop_site_no) > 0);
            $Owrd_Hash{$coop_site_no}{'agency_cd'} = $agency_cd if(length($agency_cd) > 0);
            $Owrd_Hash{$coop_site_no}{'site_no'}   = $site_no   if(length($site_no) > 0);
            $Owrd_Hash{$coop_site_no}{'cdwr_id'}   = $site_no   if(length($cdwr_id) > 0);
           }

         $Cdwr_Hash{$cdwr_id}                   = $site_id   if(length($cdwr_id) > 0);
        }
     }
  }

else
  { 
   my $message = "Collection file $collection_file does not exist";
   $screen_logger->info($message);
  }
         
# Rerieve OWRD record [all possible records at one time]
#
my $owrd_gwlevel_ref = undef;
if(defined($owrd_file))
  {
   $owrd_gwlevel_ref = getOwrdFile(\%Owrd_Hash);
  }
         
# Write a collection file
#
move("waterlevels.txt","waterlevels.backup");
my $fh = IO::File->new("waterlevels.txt", "w");
if(defined $fh)
  {
   # Print header
   #
   my $ncol  = 90;
   my $title = "U.S. Geological Survey";
      
   my $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
      
   printf ($fh $fmt," ",$title); 
      
   $title = "Klamath Groundwater Measurements";
      
   $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
      
   printf ($fh $fmt," ",$title); 
      
   $title = ucfirst($version) . "  " . $version_date;
      
   $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
      
   printf ($fh $fmt," ",$title); 
       
   printf ($fh "#\n");
       
   printf ($fh "#\n");
      
   $title = localtime;      
      
   $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
   printf($fh $fmt," ",$title);
             
   printf($fh "#\n");
      
   printf($fh "#");
   for(my $i=1; $i<=$ncol; $i++)
      { 
       printf ($fh "%s","="); 
      } 
   printf($fh "\n");

   my $line = join("\t", @lev_columns);
   printf($fh "%s\n", $line);

   $line = join("\t", @lev_formats);
   printf($fh "%s\n", $line);
  }

if(defined($logging))
  {
   print "Logging\n";
   # Print header
   #
   my $ncol  = 180;
   my $title = "U.S. Geological Survey";
      
   my $fmt = "%" . int($ncol/2-length($title)/2) . "s%s\n";
      
   my $line = sprintf($fmt,"# ",$title); 
   $file_logger->info($line);
      
   $title = "Klamath Groundwater Measurements";
      
   $fmt = "%" . int($ncol/2-length($title)/2) . "s%s\n";
      
   $line = sprintf($fmt,"# ",$title); 
   $file_logger->info($line);
      
   $title = ucfirst($version) . "  " . $version_date;
      
   $fmt = "%" . int($ncol/2-length($title)/2) . "s%s\n";
      
   $line = sprintf($fmt,"# ",$title); 
   $file_logger->info($line);
       
   $file_logger->info("#\n");

   $file_logger->info("#\n");
      
   $title = localtime;      
      
   $fmt = "%" . int($ncol/2-length($title)/2) . "s%s\n";
   $line = sprintf($fmt,"# ",$title); 
   $file_logger->info($line);
             
   $file_logger->info("#\n");
      
   $line = "#";
   for(my $i=1; $i<=$ncol; $i++)
      { 
       $line .= "=";
      } 
   $line .= "\n";
   $file_logger->info($line);

   $line  = "#"; 
   $line .= sprintf("%15s  ", "Site ID"); 
   $line .= sprintf("%15s  ", "Agency Code"); 
   $line .= sprintf("%15s  ", "Site Number"); 
   $line .= sprintf("%15s  ", "Well Log ID"); 
   $line .= sprintf("%15s  ", "CDWR ID"); 
   $line .= sprintf("%10s  ", "USGS"); 
   $line .= sprintf("%10s  ", "OWRD"); 
   $line .= sprintf("%10s  ", "CDWR"); 
   $line .= sprintf("%15s  ", "Start Date"); 
   $line .= sprintf("%15s  ", "End Date"); 
   $file_logger->info($line);
      
   $line = "#";
   for(my $i=1; $i<=$ncol; $i++)
      { 
       $line .= "=";
      } 
   $line .= "\n";
   $file_logger->info($line);
  }
   
# Build water-level records
# 
foreach my $site_id (sort keys %Site_Hash)
  {
   my $agency_cd    = $Site_Hash{$site_id}{'agency_cd'};
   my $site_no      = $Site_Hash{$site_id}{'site_no'};
   my $coop_site_no = $Site_Hash{$site_id}{'coop_site_no'};
   my $cdwr_id      = $Site_Hash{$site_id}{'cdwr_id'};
         
   # Rerieve USGS record
   #
   my $usgs_ref = undef;
   if(defined($usgs_file))
     {
      if(length($site_no) > 0)
        {
         $agency_cd = "USGS" if($agency_cd =~ /^OWRD$/i);
         $usgs_ref  = getUsgsInfo($site_id, $agency_cd, $site_no, $coop_site_no, $cdwr_id);
        }
     }

   # Rerieve OWRD record
   #
   my $owrd_ref = undef;
   if(defined($owrd_file))
     {
      if(length($coop_site_no) > 0)
        {
         $owrd_ref = getOwrdInfo($site_id, $agency_cd, $site_no, $coop_site_no, $cdwr_id, $owrd_gwlevel_ref);
        }
     }
         
   # Rerieve CDWR record
   #
   my $cdwr_ref = undef;
   if(defined($cdwr_file))
     {
      if(length($cdwr_id) > 0)
        {
         $cdwr_ref = getCdwrInfo($site_id, $agency_cd, $site_no, $coop_site_no, $cdwr_id);
        }
     }

   # Organize records
   #
   my $gwlevels_ref = undef;

   # Set USGS information
   #
   my $usgs_count = 0;
   if(defined($usgs_ref))
     {
      $gwlevels_ref = $usgs_ref;
      $usgs_count   = scalar(keys %{$usgs_ref});
     }
               
   # Organize record with OWRD information
   #
   my $owrd_count = 0;
   if(defined($owrd_ref))
     {
      if(defined($gwlevels_ref))
        {
         foreach my $days (sort keys %{$gwlevels_ref})
           {
            if(defined($owrd_ref->{$days}))
              {
               delete $owrd_ref->{$days};
              }
           }
         foreach my $days (sort keys %{$owrd_ref})
           {
            $gwlevels_ref->{$days} = $owrd_ref->{$days};
            $owrd_count++;
           }
        }
      else
        {
         $gwlevels_ref = $owrd_ref;
         $owrd_count   = scalar(keys %{$owrd_ref});
        }
     }
               
   # Organize record with CDWR information
   #
   my $cdwr_count = 0;
   if(defined($cdwr_ref))
     {
      if(defined($gwlevels_ref))
        {
         foreach my $days (sort keys %{$gwlevels_ref})
           {
            if(defined($cdwr_ref->{$days}))
              {
               delete $cdwr_ref->{$days};
              }
           }
         foreach my $days (sort keys %{$cdwr_ref})
           {
            $gwlevels_ref->{$days} = $cdwr_ref->{$days};
            $cdwr_count++;
           }
        }
      else
        {
         $gwlevels_ref = $cdwr_ref;
         $cdwr_count   = scalar(keys %{$cdwr_ref});
        }
     }
               
   # Write record
   #
   my $start_date = "";
   my $end_date   = "";
   if(defined($gwlevels_ref))
     {
      foreach my $days (sort keys %{$gwlevels_ref})
        {
         my $line = $gwlevels_ref->{$days};
         $line    =~ s/\|/\t/g;
         printf($fh "%s\n", $line);
         my ($year, $month ,$day) = Add_Delta_Days(1,1,1, $days - 1);
         $start_date = sprintf("%02s/%02s/%04s", $month ,$day, $year) if(length($start_date) < 1);
         $end_date   = sprintf("%02s/%02s/%04s", $month ,$day, $year);
        }
     }


   if(defined($logging))
     {
      my $line = " "; 
      $line   .= sprintf("%15s  ", $site_id); 
      $line   .= sprintf("%15s  ", $agency_cd); 
      $line   .= sprintf("%15s  ", $site_no); 
      $line   .= sprintf("%15s  ", $coop_site_no); 
      $line   .= sprintf("%15s  ", $cdwr_id); 
      $line   .= sprintf("%10s  ", $usgs_count); 
      $line   .= sprintf("%10s  ", $owrd_count); 
      $line   .= sprintf("%10s  ", $cdwr_count); 
      $line   .= sprintf("%15s  ", $start_date); 
      $line   .= sprintf("%15s  ", $end_date); 
      $file_logger->info("$line\n");
     }
  }

# Finished
#
exit(0); 
 

#         Subroutines
#
#===============================================================

=item I<getUsgsInfo>

 This INTERNAL subroutine is retrieve a site record from NwisWeb.

 Input:
   $site_id          -- Unique site number
   $agency_cd        -- NWIS agency code
   $site_no          -- NWIS site number
   $coop_site_no     -- NWIS cooperator site number
   $cdwr_id          -- CDWR site number

 Output:
   $rdb_ref          -- Reference to HASH that contains the levels

=cut

sub getUsgsInfo {

  my $site_id        = shift;
  my $agency_cd      = shift;
  my $site_no        = shift;
  my $coop_site_no   = shift;
  my $cdwr_id        = shift;
  
  $screen_logger->info("getUsgsInfo(): agency_cd: $agency_cd site_no: $site_no ");
  
  use LWP;
   
  # Set
  #
  my $number_of_mts   = 0;
  my $accounting_only = 0;
  my $report_ref      = undef;
   
  # Build site service url
  #
  my $url  = "http://dev.waterservices.usgs.gov/nwis/gwlevels/?";
  $url    .= join("&", (
                        "format=rdb", 
                        "agencyCd=" . uc($agency_cd), 
                        "startDT=1900-12-01",
                        "sites=$site_no"
                 ));
 
  $screen_logger->debug("getUsgsInfo(): Request for site information: $url ");

  # Request site record
  #
  my $rdb_ref  = undef;
  my $agent    = LWP::UserAgent->new;
  my $request  = HTTP::Request->new(GET => $url);
  my $response = $agent->request($request);
  $agent->timeout([10]);

  # Failed request
  #
  if(!$response->is_success)
    {
     my $rdb_ref      = undef;

     my $warn_message = "\n";
     $warn_message   .= " Error requesting site service for site $agency_cd $site_no\n";
     $warn_message   .= "  message: ";
     $warn_message   .= $response->status_line . "\n";
     $screen_logger->info($warn_message);

     return $rdb_ref;
    }

  # Content of RDB file
  #
  my $content = $response->content;

  # Build column names
  # 
  my @columns        = ();
  my @formats        = ();
  my @WANTED_COLUMNS = (
                        "agency_cd",       #  Agency Code
                        "site_no",         #  USGS site number
                        "site_tp_cd",      #  Site Type Code
                        "lev_dt",          #  Date level measured
                        "lev_tm",          #  Time level measured
                        "lev_tz_cd",       #  Time datum
                        "lev_dt_acy_cd",   #  Date/Time Significance Code
                        "lev_va",          #  Water level value in feet below land surface
                        "sl_lev_va",       #  Water level value in feet above specific vertical datum
                        "sl_datum_cd",     #  Referenced vertical datum
                        "lev_status_cd",   #  The status of the site at the time the water level was measured
                        "lev_meth_cd",     #  Method of measurement
                        "lev_agency_cd",   #  The agency code of the person measuring the water level
                        "lev_src_cd",      #  Water-level source
                        "lev_age_cd",      #  Water Level Approval Status Code
                       );

  # No reply
  #
  if(not defined($content))
    {
     my $warn_message = "Error: Web request failed for site $agency_cd $site_no \n\t $url";
     $screen_logger->info($warn_message);
    }

  # Bad reply
  #
  if($content =~ /error:/i)
    {
     my $warn_message = "Error returned from web request failed for site $agency_cd $site_no";
     $screen_logger->info($warn_message);
    }

  # Good reply
  #
  else
    {
     # Parse RDB stream
     #
     my @Lines = split(/\r?\n/, $content);

     # No records
     #
     if(scalar(@Lines) < 1)
       {
        my $warn_message = "Error: no records returned for site $agency_cd $site_no";
        $screen_logger->info($warn_message);
       }

     # Parse columns and formats
     #
     while (scalar(@Lines) > 0)
       {
        my $Line = shift @Lines;

        # Column and format lines
        #
        if($Line !~ m/^\#/)
          {
           chomp $Line;
           @columns = split("\t", $Line);
           $Line = shift @Lines;
           @formats = split("\t", $Line);
           last;
          }
       }

     # Parse information
     #
     if(scalar(@Lines) > 0)
       {
        while(scalar(@Lines) > 0)
          {
           my $Line              = shift @Lines;
           chomp $Line;
           #print "Line -> $Line\n";

           # Parse a record
           #
           my %row               = ();
           @row{@columns}        = split("\t", $Line);

           # Loop through columns
           #
           foreach my $column (@WANTED_COLUMNS)
             {
              $row{$column} = "" if(not defined($row{$column}));
             }

           # Water-level value
           #
           my $lev_va            = $row{'lev_va'};
           $lev_va               = $row{'lev_va'} if(length($row{'lev_va'}) > 0);
           my $lev_acy_cd        = "0";

           # Water-level date
           #
           my $lev_dt            = $row{'lev_dt'};
           $lev_dt               = $row{'lev_dt'} if(length($row{'lev_dt'}) > 0);
           my ($year, $month, $day) = split("-", $lev_dt);

           # Water-level time
           #
           my $lev_tm            = "";
           $lev_tm               = $row{'lev_tm'} if(length($row{'lev_tm'}) > 0);
           my ($hour, $minute)   = split(":", $lev_tm);

           # Time zone
           #
           my $lev_tz_cd         = "";
           $lev_tz_cd            = $row{'lev_tz_cd'} if(length($row{'lev_tz_cd'}) > 0);

           # Date/Time Significance Code
           #
           my $lev_dt_acy_cd     = "";
           $lev_dt_acy_cd        = $row{'lev_dt_acy_cd'} if(length($row{'lev_dt_acy_cd'}) > 0);

           # Reformat date and time into two separate columns
           #
           my $lev_str_dt     = &reformat_date_time($row{'lev_dt'},$row{'lev_tm'},$row{'lev_dt_acy_cd'});

           # Full date and time set to UTC
           #
           $month              ||= "01"; 
           $day                ||= "01"; 
           $hour               ||= "12"; 
           $minute             ||= "00"; 
           my $lev_dtm           = sprintf("%04s-%02s-%02s %02s%02s", $year, $month, $day, $hour, $minute);
           $lev_dtm             .= " $lev_tz_cd"     if(length($lev_tz_cd) > 0);

           my $lev_date          = sprintf("%04s%02s%02s", $year, $month, $day);
           my $lev_time          = sprintf("%02s%02s%02s", $hour, $minute, "0");
              
           # Measurement index
           #
           my $epoch_dt          = &datetime2epoch($lev_date, $lev_time, $lev_tz_cd);

           my $days              = Date_to_Days($year, $month, $day);

           # Water-level status
           #
           my $lev_status_cd     = "";
           $lev_status_cd        = $row{'lev_status_cd'} if(length($row{'lev_status_cd'}) > 0);

           # Method of measurement
           #
           my $lev_meth_cd       = "";
           $lev_meth_cd          = $row{'lev_meth_cd'} if(length($row{'lev_meth_cd'}) > 0);

           # Water-level source
           #
           my $lev_src_cd        = "";
           $lev_src_cd           = $row{'lev_src_cd'} if(length($row{'lev_src_cd'}) > 0);

           # The agency code of the person measuring the water level
           #
           my $lev_agency_cd     = "";
           $lev_agency_cd        = $row{'lev_agency_cd'} if(length($row{'lev_agency_cd'}) > 0);

           $row{'site_id'}       = $site_id;
           $row{'agency_cd'}     = $agency_cd;
           $row{'site_no'}       = $site_no;
           $row{'coop_site_no'}  = $coop_site_no;
           $row{'cdwr_id'}       = $cdwr_id;

           $row{'lev_va'}        = $lev_va;
           $row{'lev_acy_cd'}    = $lev_acy_cd;
           $row{'lev_dtm'}       = $lev_dtm;
           $row{'lev_dt'}        = $lev_dt;
           $row{'lev_tm'}        = $lev_tm;
           $row{'lev_tz_cd'}     = $lev_tz_cd;
           $row{'lev_dt_acy_cd'} = $lev_dt_acy_cd;
           $row{'lev_str_dt'}    = $lev_str_dt;
           $row{'lev_status_cd'} = $lev_status_cd;
           $row{'lev_meth_cd'}   = $lev_meth_cd;
           $row{'lev_agency_cd'} = $lev_agency_cd;
           $row{'lev_src_cd'}    = $lev_src_cd;
           $row{'lev_status_cd'} = $lev_status_cd;
           $row{'lev_rmk_tx'}    = "";

           $row{'record'}        = join("|", @row{@lev_columns});
           
           # Valid measurement [must have valid record for lev_va and lev_status]
           #
           my $record_flag       = "Y";

           $record_flag          = "N" if(length($lev_va) < 1);
           $record_flag          = "N" if($lev_status_cd ne "");
           $record_flag          = "Y" if(length($lev_va) > 0 and $lev_status_cd eq "C");
           $record_flag          = "N" if($lev_src_cd eq "D");
   
           if($record_flag eq "Y")
             {
              $rdb_ref->{$days} = $row{'record'};
             }
                
           push(@{$report_ref->{$days}},@row{@columns});
          }
       }

     else
       {
        my $warn_message = "Error: no record returned for site $agency_cd $site_no";
        $screen_logger->info($warn_message);
       }
    }

  # Log records
  #
  if(defined($report))
    {
     my $fh = IO::File->new("usgs_${site_no}.txt", "w");
     if(defined $fh)
       {
        # Print header
        #
        my $ncol  = 90;
        my $title = "U.S. Geological Survey";
         
        my $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
         
        printf ($fh $fmt," ",$title); 
         
        $title = "USGS Groundwater Measurements";
         
        $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
         
        printf ($fh $fmt," ",$title); 
         
        $title = ucfirst($version) . "  " . $version_date;
         
        $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
         
        printf ($fh $fmt," ",$title); 
          
        printf ($fh "#\n");
          
        printf ($fh "#\n");
         
        $title = localtime;      
         
        $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
        printf($fh $fmt," ",$title);
               
        printf($fh "#\n");
         
        printf($fh "#");
        for(my $i=1; $i<=$ncol; $i++) { 
            printf ($fh "%s","="); 
         } 
        printf($fh "\n");
   
        my $line = join("\t", @columns);
        printf($fh "%s\n", $line);
   
        $line = join("\t", @formats);
        printf($fh "%s\n", $line);
   
        foreach my $days (sort keys %$report_ref)
          {
           $number_of_mts++;
   
           # Join
           #
           my $line = join("\t", @{$report_ref->{$days}});
           printf($fh "%s\n", $line);
          }
        $fh->close;
       }
    }
        
  my $warn_message = "For site $agency_cd $site_no found $number_of_mts records [ommitted $accounting_only]";
  $screen_logger->debug($warn_message);
     
  return $rdb_ref;
 
}

############################################################

=item I<getOwrdFile>

 This INTERNAL subroutine is retrieve all water-level records from OWRD.

 Input:
   $sites_ref   -- Hash reference to list of OWRD sites

 Output:
   $rdb_ref     -- Reference to HASH that contains the levels

=cut

sub getOwrdFile {

  my $sites_ref = shift;
  
  $screen_logger->info("getOwrdFile()");
  
  use LWP;

  # Set
  #
  my $number_of_sites = 0;
  my $number_of_mts   = 0;
  my $number_of_only  = 0;
  my %Sites           = ();
  my $report_ref      = undef;
   
  # Build site service url
  #
  my $url  = "http://filepickup.wrd.state.or.us/files/Publications/obswells/data/owrd_wls.txt";
  $screen_logger->debug("getOwrdInfo(): Request for site information: $url ");

  # Request site record
  #
  my $rdb_ref  = undef;
  my $agent    = LWP::UserAgent->new;
  my $request  = HTTP::Request->new(GET => $url);
  my $response = $agent->request($request);
  $agent->timeout([10]);

  # Failed request
  #
  if(!$response->is_success)
    {
     my $rdb_ref      = undef;

     my $warn_message = " Error (" . $response->status_line . ") in requesting OWRD waterlevel file";
     $screen_logger->info($warn_message);

     return $rdb_ref;
    }

  # Content of RDB file
  #
  my $content = $response->content;

  # Build column names
  # 
  my @data_fields = (
                     ['Logid',              'coop_site_no',    '10s'],
                     ['Date',               'lev_dt',          '15s'],
                     ['Time',               'lev_tm',          '10s'],
                     ['WlBlsd',             'lev_va',          '10s'],
                     ['Method',             'lev_meth_cd',      '1s'],
                     ['Status',             'lev_status_cd',    '1s'],
                     ['SourceOrg',          'lev_agency_cd',   '20s'],
                     ['SourceOWRD',         'lev_src_cd',       '1s'],
                     ['WlComments',         'lev_rmk_tx',     '100s']
                    );

  # Build output column names
  #
  my @columns        = ();
  my @formats        = ();
  my @WANTED_COLUMNS = map { $_->[0] } @data_fields;
  my @USGS_COLUMNS   = map { $_->[1] } @data_fields;
  my @WANTED_FORMATS = map { $_->[2] } @data_fields;

  # No reply
  #
  if(not defined($content))
    {
     my $warn_message = "Error: Web request failed for retrieving OWRD file \n\t $url";
     $screen_logger->info($warn_message);
    }

  # Bad reply
  #
  if($content =~ /error:/i)
    {
     my $warn_message = "Error returned from web request failed for retrieving OWRD file";
     $screen_logger->info($warn_message);
    }

  # Good reply
  #
  else
    {
     # Parse RDB stream
     #
     my @Lines = split("\n",$content);

     # No records
     #
     if(scalar(@Lines) < 1)
       {
        my $warn_message = "Error: no records returned for OWRD file";
        $screen_logger->info($warn_message);
       }

     # Parse columns and formats
     #
     while (scalar(@Lines) > 0)
       {
        my $Line = shift @Lines;

        # Column and format lines
        #
        if($Line !~ m/^\#/)
          {
           chomp $Line;
           @columns = split("\t", $Line);
           last;
          }
       }

     # Parse site information
     #
     while (scalar(@Lines) > 0)
       {
        my $Line = shift @Lines;
        chomp $Line;

        # Parse a record
        #
        my %row           = ();
        @row{@columns}    = split("\t", $Line);

        my $coop_site_no  = $row{'Logid'};

        # Check if site is in collection
        #
        if(defined($sites_ref->{$coop_site_no}->{'site_id'}))
          {
           my $site_id   = $sites_ref->{$coop_site_no}->{'site_id'};
           my $agency_cd = $sites_ref->{$coop_site_no}->{'agency_cd'};
           my $site_no   = $sites_ref->{$coop_site_no}->{'site_no'};
           my $cdwr_id   = $sites_ref->{$coop_site_no}->{'cdwr_id'};

           $number_of_sites++ if(not defined($Sites{$coop_site_no}));
           $number_of_mts++;
           $Sites{$coop_site_no} = 1;

           # Loop through columns
           #
           foreach my $column_ref (@data_fields)
             {
              $row{$column_ref->[1]} = "";
              $row{$column_ref->[1]} = $row{$column_ref->[0]} if(defined($row{$column_ref->[0]}));
             }

           # Water-level
           #
           my $lev_va               = "";
           $lev_va                  = $row{'lev_va'} if(length($row{'lev_va'}) > 0);

           # Water-level date
           #
           my $lev_dt               = "";
           $lev_dt                  = $row{'lev_dt'} if(length($row{'lev_dt'}) > 0);
           
           # Reformat water-level date
           #
           my $lev_dt_acy_cd        = "Y";
           my ($month, $day, $year) = split("/", $lev_dt);

           my $lev_str_dt           = $year;
           $lev_str_dt             .= "-$month" if(defined($month));
           $lev_str_dt             .= "-$day"   if(defined($day));

           $lev_dt                  = $lev_str_dt;

           $lev_dt_acy_cd           = "M" if(defined($month));
           $lev_dt_acy_cd           = "D" if(defined($day));
           $month                 ||= "01";
           $day                   ||= "01";

           my $lev_dtm              = sprintf("%04s-%02s-%02s", $year, $month, $day);

           my $lev_date          = sprintf("%04s%02s%02s", $year, $month, $day);

#           $lev_dt                  = sprintf("%02d-%.3s-%d", $day, Month_to_Text($month), $year);
#           $lev_str_dt              = sprintf("%02s/%02s/%04s", $month,$day,$year);

           # Water-level time
           #
           my $lev_tm            = "";
           $lev_tm               = $row{'lev_tm'} if(length($row{'lev_tm'}) > 0);
           my ($hour, $minute, $second) = split(":", $lev_tm);
           $lev_tm               = sprintf("%02s%02s", $hour, $minute) if(length($lev_tm) > 0);
           $lev_str_dt          .= " $lev_tm"     if(length($row{'lev_tm'}) > 0);
           $lev_dt_acy_cd        = "H" if(defined($hour));
           $hour               ||= "12"; 
           $lev_dt_acy_cd        = "m" if(defined($minute));
           $minute             ||= "00"; 

           $lev_dtm             .= sprintf(" %02s%02s", $hour, $minute);

           my $lev_time          = sprintf("%02s%02s%02s", $hour, $minute, "0");

           my $lev_tz_cd         = "PST";
           #$lev_tz_cd            = $row{'lev_tz_cd'} if(length($row{'lev_tz_cd'}) > 0);
           $lev_str_dt          .= " $lev_tz_cd"     if(length($lev_tz_cd) > 0);
              
           # Measurement index
           #
           my $epoch_dt          = &datetime2epoch($lev_date, $lev_time, $lev_tz_cd);

           my $days              = Date_to_Days($year, $month, $day);

           # Convert OWRD string to NWIS codes for lev_meth_cd
           #
           my $lev_meth_cd = "";
           $lev_meth_cd    = $row{'lev_meth_cd'} if(length($row{'lev_meth_cd'}) > 0);

           $lev_meth_cd = "R" if($lev_meth_cd eq "");
           $lev_meth_cd = "A" if($lev_meth_cd =~ m/AIRLINE/i);
           $lev_meth_cd = "L" if($lev_meth_cd =~ m/CAMERA/i);
           $lev_meth_cd = "T" if($lev_meth_cd =~ m/ETAPE/i);
           $lev_meth_cd = "V" if($lev_meth_cd =~ m/ETAPE/i and $lev_meth_cd =~ m/CALIBRATED/i);
           $lev_meth_cd = "G" if($lev_meth_cd =~ m/GAGE/i);
           $lev_meth_cd = "H" if($lev_meth_cd =~ m/GAGE/i and $lev_meth_cd =~ m/CALIBRATED/i);
           $lev_meth_cd = "M" if($lev_meth_cd =~ m/MANOMETER/i);
           $lev_meth_cd = "O" if($lev_meth_cd =~ m/OBSERVED/i);
           $lev_meth_cd = "Z" if($lev_meth_cd =~ m/OTHER/i);
           $lev_meth_cd = "B" if($lev_meth_cd =~ m/RECORDER/i and $lev_meth_cd =~ m/DIGITAL/i);
           $lev_meth_cd = "B" if($lev_meth_cd =~ m/RECORDER/i and $lev_meth_cd =~ m/ANALOG/i);
           $lev_meth_cd = "B" if($lev_meth_cd =~ m/RECORDER/i and $lev_meth_cd =~ m/SHAFT ENC/i);
           $lev_meth_cd = "F" if($lev_meth_cd =~ m/RECORDER/i and $lev_meth_cd =~ m/TRANSD/i);
           $lev_meth_cd = "R" if($lev_meth_cd =~ m/REPORTED/i);
           $lev_meth_cd = "S" if($lev_meth_cd =~ m/TAPE/i);
           $lev_meth_cd = "S" if($lev_meth_cd =~ m/STEEL TAPE/i);
           $lev_meth_cd = "R" if($lev_meth_cd =~ m/TO RESEARCH/i);
           $lev_meth_cd = "R" if($lev_meth_cd =~ m/UNKNOWN|OTHER/i);
           $lev_meth_cd = "E" if($lev_meth_cd =~ m/ESTIMATED/i);
           $lev_meth_cd = "F" if($lev_meth_cd =~ m/SONIC|TRANSDUCER/i);
           $lev_meth_cd = "L" if($lev_meth_cd =~ m/GEOPHYSICAL LOG/i);

           # Accounting-only records [method NOT MEASURED]
           #
           if($lev_meth_cd =~ m/NOT MEASURED/i)
             {
              $number_of_only++;
              next;
             } 

           # Correct method for flat e-tape in wl comments
           #
           my $lev_rmk_tx = "";
           $lev_rmk_tx    = $row{'lev_rmk_tx'} if(length($row{'lev_rmk_tx'}) > 0);
           $lev_meth_cd   = "V" if($lev_rmk_tx =~ m/Flat E-Tape/i);
             
           if($lev_meth_cd eq "A" or
              $lev_meth_cd eq "B" or
              $lev_meth_cd eq "C" or
              $lev_meth_cd eq "E" or
              $lev_meth_cd eq "F" or
              $lev_meth_cd eq "G" or
              $lev_meth_cd eq "H" or
              $lev_meth_cd eq "L" or
              $lev_meth_cd eq "M" or
              $lev_meth_cd eq "N" or
              $lev_meth_cd eq "O" or
              $lev_meth_cd eq "P" or
              $lev_meth_cd eq "R" or
              $lev_meth_cd eq "S" or
              $lev_meth_cd eq "T" or
              $lev_meth_cd eq "U" or
              $lev_meth_cd eq "V" or
              $lev_meth_cd eq "Z") {
           } else {
              #printf (ERRORFILE $format,$Otherid,$Coopid,$Site_ID,$Levval,$Levdate,$Levtime,"Invalid method ($lev_meth_cd) for water-level measurement");
              print "\n Site $coop_site_no: Invalid method ($lev_meth_cd) for water-level measurement at $lev_dt \n";
              next;
           }
   
           # Water level source
           # 
           my $lev_agency_cd = "";
           my $lev_src_cd    = "";
           my $sourceowrd    = "";
           $lev_src_cd       = $row{'SourceOrg'}  if(length($row{'SourceOrg'}) > 0);
           $sourceowrd       = $row{'SourceOWRD'} if(length($row{'SourceOWRD'}) > 0);
             
           if($lev_src_cd =~ m/USGS/i) {
              $lev_agency_cd = "USGS";
              $lev_src_cd    = "S";
           }
           elsif($lev_src_cd =~ m/^BLM$/i) {
              $lev_agency_cd = "OR045";
              $lev_src_cd    = "A";
           }
           elsif($lev_src_cd =~ m/^USACE$/i) {
              $lev_agency_cd = "USCE";
              $lev_src_cd    = "A";
           }
           elsif($lev_src_cd =~ m/OWRD/i)
             {
              $lev_agency_cd = "OR004";
              $lev_src_cd    = "A";
              if($sourceowrd =~ m/WELL LOG/i)
                {
                 $lev_src_cd    = "D";
                 $lev_meth_cd   = "R";
                }
              if($sourceowrd =~ m/UNKNOWN/i)
                {
                 $lev_agency_cd = "OR004";
                 $lev_src_cd    = "A";
                 $lev_meth_cd   = "R";
                }
             }
           elsif($lev_src_cd =~ m/UNKNOWN/i) {
              $lev_agency_cd = "OR004";
              $lev_src_cd    = "A";
              $lev_meth_cd   = "R";
           }
           elsif($lev_src_cd =~ m/DOGAMI/i) {
              $lev_agency_cd = "OR046";
              $lev_src_cd    = "A";
              $lev_meth_cd   = "R";
           }
           elsif($lev_src_cd =~ m/HEALTH DIV/i) {
              $lev_agency_cd = "OR004";
              $lev_src_cd    = "A";
              $lev_meth_cd   = "R";
           }
           elsif($lev_src_cd =~ m/DRILLER/i or $lev_src_cd =~ m/PUMP INSTALLER/i) {
              $lev_agency_cd = "OR004";
              $lev_src_cd    = "D";
              $lev_meth_cd   = "R";
           }
           elsif($lev_src_cd =~ m/WELL LOG/i) {
              $lev_agency_cd = "OR004";
              $lev_src_cd    = "D";
              $lev_meth_cd   = "R";
           }
           elsif($lev_src_cd =~ m/OWNER/i or
              $lev_src_cd =~ m/GAGE/i or
              $lev_src_cd =~ m/GAGE OWNER/i) {
              $lev_agency_cd = "OR004";
              $lev_src_cd    = "O";
              $lev_meth_cd   = "R";
           }
           elsif($lev_src_cd =~ m/OTHER/i) {
              $lev_agency_cd = "OR004";
              $lev_src_cd = "Z";
              $lev_meth_cd = "R";
           }
           elsif($lev_src_cd =~ m/^OR STATE UNIV/i) {
              $lev_agency_cd = "OR051";
              $lev_src_cd = "A";
              $lev_meth_cd = "R";
           }
           elsif($lev_src_cd =~ m/CONSULTANT/i or
              $lev_src_cd =~ m/^RG$/i                   or
              $lev_src_cd =~ m/^PE$/i                   or
              $lev_src_cd =~ m/^CEG$/i                  or
              $lev_src_cd =~ m/^RPG$/i                  or
              $lev_src_cd =~ m/^IRZ$/i                  or
              $lev_src_cd =~ m/^CWRE$/i                   ) {
              $lev_agency_cd = "OR004";
              $lev_src_cd = "G";
              $lev_meth_cd = "R";
           }
           elsif($lev_src_cd =~ m/TUAL VALLEY IRR DIST/i or
              $lev_src_cd =~ m/BONANZA WELL ASSOC/i or
              $lev_src_cd =~ m/RGP/i     ) {
              $lev_agency_cd = "OR004";
              $lev_src_cd = "R";
              $lev_meth_cd = "R";
           }
           else {
              #printf (ERRORFILE $format,$Otherid,$Coopid,$Site_ID,$Levval,$Levdate,$Levtime,"Invalid source of water-level measurement ($lev_src_cd)");
              print "\n Site $coop_site_no: Invalid source of water-level measurement ($lev_src_cd) at $lev_dt \n";
           }
 
           # Water level status
           # 
           my $lev_status_cd = "";
           $lev_status_cd    = $row{'lev_status_cd'} if(length($row{'lev_status_cd'}) > 0);
              
           $lev_status_cd = "D" if($lev_status_cd =~ m/DRY/i);
           $lev_status_cd = "J" if($lev_status_cd =~ m/INJECT/i);
           $lev_status_cd = "S" if($lev_status_cd =~ m/FALLING/i);
           $lev_status_cd = "F" if($lev_status_cd =~ m/FLOWING/i);
           $lev_status_cd = "P" if($lev_status_cd =~ m/PUMPING/i);
           $lev_status_cd = "R" if($lev_status_cd =~ m/RISING/i);
           $lev_status_cd = ""  if($lev_status_cd =~ m/STATIC/i);
           $lev_status_cd = ""  if($lev_status_cd =~ m/TO RESEARCH/i);
           $lev_status_cd = ""  if($lev_status_cd =~ m/UNKNOWN/i);
           $lev_status_cd = ""  if($lev_status_cd =~ m/OTHER/i and $lev_agency_cd eq "USGS");
           $lev_status_cd = "Z" if($lev_status_cd =~ m/OTHER/i and $lev_agency_cd ne "USGS");
             
           if($lev_status_cd =~ m/^(D|J|S|E|F|P|R|S|T|V|W|Z)$/ or $lev_status_cd eq "") {
                    
           } else {
              #printf (ERRORFILE $format,$Otherid,$Coopid,$Site_ID,$Levval,$Levdate,$Levtime,"Invalid status ($lev_status_cd) for water-level measurement");
              print "\n Site $coop_site_no: Invalid status ($lev_status_cd) for water-level measurement at $lev_dt\n";
           }
 
           # Water level accuracy
           # 
           my $lev_acy_cd = "";
           if($lev_acy_cd eq "") {
             if($lev_meth_cd ne "" and $lev_meth_cd ne "--") {
               if($lev_meth_cd eq "A" or 
                  $lev_meth_cd eq "E" or 
                  $lev_meth_cd eq "G" or 
                  $lev_meth_cd eq "O" or 
                  $lev_meth_cd eq "R" or 
                  $lev_meth_cd eq "U" or
                  $lev_meth_cd eq "Z" ) {
                  $lev_acy_cd = 0;
               }
               if($lev_meth_cd eq "B" or 
                  $lev_meth_cd eq "C" or 
                  $lev_meth_cd eq "H" or 
                  $lev_meth_cd eq "L" or 
                  $lev_meth_cd eq "T" ) {
                  $lev_acy_cd = 1;
               }
               if($lev_meth_cd eq "S" or 
                  $lev_meth_cd eq "V" ) {
                  $lev_acy_cd = 2;
               }
             }
           } 
                    
           # Water-level measurement
           # 
           $row{'site_id'}       = $site_id;
           $row{'agency_cd'}     = $agency_cd;
           $row{'site_no'}       = $site_no;
           $row{'coop_site_no'}  = $coop_site_no;
           $row{'cdwr_id'}       = $cdwr_id;

           $row{'lev_va'}        = $lev_va;
           $row{'lev_acy_cd'}    = $lev_acy_cd;
           $row{'lev_dtm'}       = $lev_dtm;
           $row{'lev_dt'}        = $lev_dt;
           $row{'lev_tm'}        = $lev_tm;
           $row{'lev_tz_cd'}     = $lev_tz_cd;
           $row{'lev_dt_acy_cd'} = $lev_dt_acy_cd;
           $row{'lev_str_dt'}    = $lev_str_dt;
           $row{'lev_status_cd'} = $lev_status_cd;
           $row{'lev_meth_cd'}   = $lev_meth_cd;
           $row{'lev_agency_cd'} = $lev_agency_cd;
           $row{'lev_src_cd'}    = $lev_src_cd;
           $row{'lev_rmk_tx'}    = "";

           # Valid measurement [must have valid record for lev_va and lev_status]
           #
           my $record_flag       = "Y";

           $record_flag          = "N" if($lev_status_cd ne "");
           $record_flag          = "N" if(length($lev_va) < 1);
           $record_flag          = "N" if($lev_src_cd eq "D");
           $record_flag          = "N" if($lev_src_cd eq "G");

           $row{'record'}        = join("|", map { $row{$_} ||= "" } @lev_columns);
   
           if($record_flag eq "Y")
             {
              $rdb_ref->{$coop_site_no}->{$days} = $row{'record'};
             }
              
           push(@{$report_ref->{$coop_site_no}->{$days}}, @row{@columns});
          }
       }
    }

  # Log records
  #
  if(defined($report))
    {
     foreach my $coop_site_no (sort keys %{$report_ref})
       {
        my $file = "owrd_${coop_site_no}.txt";
        $file    =~ s/ /_/g;

        my $fh = IO::File->new($file, "w");
        if(defined $fh)
          {
           # Print header
           #
           my $ncol  = 90;
           my $title = "U.S. Geological Survey";
            
           my $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
            
           printf ($fh $fmt," ",$title); 
            
           $title = "OWRD Groundwater Measurements";
            
           $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
            
           printf ($fh $fmt," ",$title); 
            
           $title = ucfirst($version) . "  " . $version_date;
            
           $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
            
           printf ($fh $fmt," ",$title); 
             
           printf ($fh "#\n");
             
           printf ($fh "#\n");
            
           $title = localtime;      
            
           $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
           printf($fh $fmt," ",$title);
                  
           printf($fh "#\n");
            
           printf($fh "#");
           for(my $i=1; $i<=$ncol; $i++) { 
               printf ($fh "%s","="); 
            } 
           printf($fh "\n");
      
           my $line = join("\t", @columns);
           printf($fh "%s\n", $line);
      
           $line = join("\t", @formats);
           printf($fh "%s\n", $line);
      
           foreach my $days (sort keys %{$report_ref->{$coop_site_no}})
             {
              # Join
              #
              my $line = join("\t", @{$report_ref->{$coop_site_no}->{$days}});
              printf($fh "%s\n", $line);
             }
           $fh->close;
          }
       }
    }
        
  my $warn_message = "Matched $number_of_mts measurements [omitted $number_of_only] for $number_of_sites sites in OWRD file";
  $screen_logger->info($warn_message);
     
  return $rdb_ref;
 
}

############################################################

=item I<getOwrdInfo>

 This INTERNAL subroutine is retrieve a site record from NwisWeb.

 Input:
   $coop_site_no -- NWIS cooperator site number

 Output:
   $rdb_ref     -- Reference to HASH that contains the levels

=cut

sub getOwrdInfo {

  my $site_id      = shift;
  my $agency_cd    = shift;
  my $site_no      = shift;
  my $coop_site_no = shift;
  my $cdwr_id      = shift;
  my $owrd_ref     = shift;
  
  $screen_logger->info("getOwrdInfo(): $coop_site_no");

  my $number_of_sites = 0;
  my $number_of_mts   = 0;
  my $number_of_only  = 0;
  my $rdb_ref;

  # Build column names
  # 
  my @data_fields = (
                     ['Logid',              'coop_site_no',    '10s'],
                     ['Date',               'lev_dt',          '15s'],
                     ['Time',               'lev_tm',          '10s'],
                     ['WlBlsd',             'lev_va',          '10s'],
                     ['Method',             'lev_meth_cd',      '1s'],
                     ['Status',             'lev_status_cd',    '1s'],
                     ['SourceOrg',          'lev_agency_cd',   '20s'],
                     ['SourceOWRD',         'lev_src_cd',       '1s'],
                     ['WlComments',         'lev_rmk_tx',     '100s']
                    );

  # Build output column names
  #
  my @WANTED_COLUMNS = map { $_->[0] } @data_fields;
  my @USGS_COLUMNS   = map { $_->[1] } @data_fields;
  my @WANTED_FORMATS = map { $_->[2] } @data_fields;

  # Loop through water-level measurements
  #
  foreach my $epoch_dt (sort keys %{$owrd_ref->{$coop_site_no}})
    {
     $number_of_mts++;
     $rdb_ref->{$epoch_dt} = $owrd_ref->{$coop_site_no}->{$epoch_dt};
    }
        
  my $warn_message = "Matched $number_of_mts measurements for site $coop_site_no";
  $screen_logger->info($warn_message);
     
  return $rdb_ref;
 
}

############################################################

=item I<getCdwrInfo>

 This INTERNAL subroutine is retrieve a site record from CDWR.

 Input:
   $cdwr_id     -- CDWR ID

 Output:
   $rdb_ref     -- Reference to HASH that contains the levels

=cut

sub getCdwrInfo {

  my $site_id        = shift;
  my $agency_cd      = shift;
  my $site_no        = shift;
  my $coop_site_no   = shift;
  my $cdwr_id        = shift;
  
  $screen_logger->info("getCdwrInfo(): Site $cdwr_id ");
  
  use LWP;
   
  # Set
  #
  my $number_of_mts   = 0;
  my $accounting_only = 0;
  my $report_ref      = undef;
   
  # Build site service url
  #
  my $url  = "http://www.water.ca.gov/waterdatalibrary/groundwater/hydrographs/report_txt_brr.cfm?";
  $url    .= join("&", ("CFGRIDKEY=$cdwr_id", 
                        "type=xcl"
                 ));
 
  $screen_logger->debug("getCdwrInfo(): Request for site information: $url ");

  # Request site record
  #
  my $rdb_ref  = undef;
  my $agent    = LWP::UserAgent->new;
  my $request  = HTTP::Request->new(GET => $url);
  my $response = $agent->request($request);
  $agent->timeout([10]);

  # Failed request
  #
  if(!$response->is_success)
    {
     my $rdb_ref      = undef;

     my $warn_message = "\n";
     $warn_message   .= " Error requesting site service for site $cdwr_id\n";
     $warn_message   .= "  message: ";
     $warn_message   .= $response->status_line . "\n";
     $screen_logger->info($warn_message);

     return $rdb_ref;
    }

  # Content of RDB file
  #
  my $content = $response->content;

  # Build column names
  # 
  my @columns        = ();
  my @formats        = ();
  my @WANTED_COLUMNS = (
                        'Station_Code',
                        'Measurement_Date',
                        'RP_Elevation',
                        'GS_Elevation',
                        'RPWS',
                        'WSE',
                        'GSWS',
                        'QM_Code',
                        'NM_Code',
                        'Agency',
                        'Comment'
                       );

  my @WANTED_FORMATS = (
                        '30s',
                        '15s',
                        '15s',
                        '15s',
                        '15s',
                        '15s',
                        '15s',
                        '1s',
                        '1s',
                        '15s',
                        '30s'
                       );

  # Build needed column names
  # 
  my @data_fields = (
                     ['Station_Code',       'station_nm'],
                     ['Measurement_Date',   'lev_dt'],
                     ['GSWS',               'lev_va'],
                     ['QM_Code',            'qm_code'],
                     ['NM_Code',            'nm_code'],
                     ['Status',             'lev_status_cd'],
                     ['Agency',             'lev_agency_cd'],
                     ['Comment',            'lev_rmk_tx']
                    );

  # No reply
  #
  if(not defined($content))
    {
     my $warn_message = "Error: Web request failed for site $cdwr_id \n\t $url";
     $screen_logger->info($warn_message);
    }

  # Bad reply
  #
  if($content =~ /error:/i)
    {
     my $warn_message = "Error returned from web request failed for site $cdwr_id";
     $screen_logger->info($warn_message);
    }

  # Good reply
  #
  else
    {
     # Parse RDB stream
     #
     my @Lines = split(/\r?\n/,$content);

     # No records
     #
     if(scalar(@Lines) < 1)
       {
        my $warn_message = "Error: no records returned for site $cdwr_id";
        $screen_logger->info($warn_message);
       }

     # Parse columns and formats
     #
     while (scalar(@Lines) > 0)
       {
        my $Line = shift @Lines;

        # Column and format lines
        #
        if($Line !~ m/^\#/)
          {
           @columns = split(",", $Line);
           last;
          }
       }

     # Parse site information
     #
     if(scalar(@Lines) > 0)
       {
        while(scalar(@Lines) > 0)
          {
           my $Line = shift @Lines;
           #print "$Line \n";

           # Parse a record
           #
           my %row               = ();
           @row{@columns}        = split(",", $Line);
           #print "Line $Line \n";

           # Loop through columns
           #
           foreach my $column_ref (@data_fields)
             {
              $row{$column_ref->[1]} = "";
              $row{$column_ref->[1]} = $row{$column_ref->[0]} if(defined($row{$column_ref->[0]}));
             }

           # Water-level value
           #
           my $lev_va            = "";
           $lev_va               = $row{'lev_va'} if(length($row{'lev_va'}) > 0);
           my $lev_acy_cd        = "0";

           # Water-level date
           #
           my $lev_dt            = "";
           $lev_dt               = $row{'lev_dt'} if(length($row{'lev_dt'}) > 0);
           my $lev_str_dt        = $row{'lev_dt'};

           my ($month, $day, $year) = split("-", $lev_dt);
           my $lev_dt_acy_cd     = "Y";

           $lev_dt_acy_cd        = "M" if(defined($month));
           $lev_dt_acy_cd        = "D" if(defined($day));
           $month              ||= "01"; 
           $day                ||= "01";

           my $lev_dtm           = sprintf("%04s-%02s-%02s", $year, $month, $day);

           my $lev_date          = sprintf("%04s%02s%02s", $year, $month, $day);

           # Water-level time
           #
           my $lev_tm            = "";
           my $hour              = "12"; 
           my $minute            = "00"; 

           $lev_dtm             .= sprintf(" %02s%02s", $hour, $minute);

           my $lev_time          = sprintf("%02s%02s%02s", $hour, $minute, "0");

           my $lev_tz_cd         = "";
              
           # Measurement index
           #
           my $epoch_dt          = &datetime2epoch($lev_date, $lev_time, $lev_tz_cd);

           my $days              = Date_to_Days($year, $month, $day);

           # Status and method
           #
           my $lev_status_cd     = "";
           my $lev_meth_cd       = "R";

           my $lev_rmk_tx        = "";
           $lev_rmk_tx           = $row{'lev_rmk_tx'} if(length($row{'lev_rmk_tx'}) > 0);
           $lev_rmk_tx           =~ s/(\"|\')//g;
              
           my $nm_code           = "";
           $nm_code              = $row{'nm_code'} if(length($row{'nm_code'}) > 0);

           my $qm_code           = "";
           $qm_code              = $row{'qm_code'} if(length($row{'qm_code'}) > 0);

           $lev_status_cd = "N" if($nm_code =~ m/0/i);
           $lev_status_cd = "P" if($nm_code =~ m/1/i);
           $lev_status_cd = "O" if($nm_code =~ m/(3|4)/i);
           $lev_status_cd = "W" if($nm_code =~ m/6/i);
           $lev_status_cd = "K" if($nm_code =~ m/8/i);
           $lev_status_cd = "D" if($nm_code =~ m/D/i);
           $lev_status_cd = "F" if($nm_code =~ m/F/i);
              
           $lev_status_cd = "P" if($qm_code =~ m/1/i);
           $lev_status_cd = "S" if($qm_code =~ m/2/i);
           $lev_status_cd = "J" if($qm_code =~ m/3/i);
           $lev_status_cd = "R" if($qm_code =~ m/4/i);
           $lev_status_cd = "J" if($qm_code =~ m/7/i);
           $lev_status_cd = "V" if($qm_code =~ m/8/i);

           $lev_meth_cd   = "A" if($qm_code =~ m/5/i);
           $lev_meth_cd   = "P" if($qm_code =~ m/9/i);
           $lev_meth_cd   = "O" if($lev_status_cd =~ m/(F|N|W)/i);

           # Agency code
           #
           my $lev_agency_cd     = "";
           $lev_agency_cd        = $row{'lev_agency_cd'} if(length($row{'lev_agency_cd'}) > 0);
           my $lev_src_cd        = "A";

           if($lev_agency_cd =~ m/^5000$/)
             {
              $lev_agency_cd     = "USGS";
             }
           elsif($lev_agency_cd =~ m/^5001$/)
             {
              $lev_agency_cd     = "US BOR";
             }
           else
             {
              $lev_agency_cd     = "CDWR";
             }           

           # Load measurement
           #
           $row{'site_id'}       = $site_id;
           $row{'agency_cd'}     = $agency_cd;
           $row{'site_no'}       = $site_no;
           $row{'coop_site_no'}  = $coop_site_no;
           $row{'cdwr_id'}       = $cdwr_id;
   
           $row{'lev_va'}        = $lev_va;
           $row{'lev_acy_cd'}    = $lev_acy_cd;
           $row{'lev_dtm'}       = $lev_dtm;
           $row{'lev_dt'}        = $lev_dt;
           $row{'lev_tm'}        = $lev_tm;
           $row{'lev_tz_cd'}     = $lev_tz_cd;
           $row{'lev_dt_acy_cd'} = $lev_dt_acy_cd;
           $row{'lev_str_dt'}    = $lev_str_dt;
           $row{'lev_status_cd'} = $lev_status_cd;
           $row{'lev_meth_cd'}   = $lev_meth_cd;
           $row{'lev_agency_cd'} = $lev_agency_cd;
           $row{'lev_src_cd'}    = $lev_src_cd;
           $row{'lev_rmk_tx'}    = $lev_rmk_tx;
   
           $row{'record'}        = join("|", @row{@lev_columns});

           # Valid measurement [must have valid record for lev_va and lev_status]
           #
           my $record_flag       = "Y";

           $record_flag          = "N" if(length($lev_va) < 1);
           $record_flag          = "N" if($lev_status_cd ne "");

           # Accounting-only measurement [no record for lev_va and lev_status]
           #
           if($record_flag eq "N")
             {
              my $warn_message = "Warning: Accounting-only record returned for site $cdwr_id on $lev_dt";
              $screen_logger->debug($warn_message);
              $accounting_only++;
             }
   
           if($record_flag eq "Y")
             {
              $rdb_ref->{$days}     = $row{'record'};
             }
                
           push(@{$report_ref->{$days}},@row{@columns});
          }
       }

     else
       {
        my $warn_message = "Error: no record returned for site $cdwr_id";
        $screen_logger->info($warn_message);
       }
    }

  # Log records
  #
  if(defined($report))
    {
     my $fh = IO::File->new("cdwr_${cdwr_id}.txt", "w");
     if(defined $fh)
       {
        # Print header
        #
        my $ncol  = 90;
        my $title = "U.S. Geological Survey";
         
        my $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
         
        printf ($fh $fmt," ",$title); 
         
        $title = "CDWR Groundwater Measurements";
         
        $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
         
        printf ($fh $fmt," ",$title); 
         
        $title = ucfirst($version) . "  " . $version_date;
         
        $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
         
        printf ($fh $fmt," ",$title); 
          
        printf ($fh "#\n");
          
        printf ($fh "#\n");
         
        $title = localtime;      
         
        $fmt = "#%" . int($ncol/2-length($title)/2) . "s%s\n";
        printf($fh $fmt," ",$title);
               
        printf($fh "#\n");
         
        printf($fh "#");
        for(my $i=1; $i<=$ncol; $i++) { 
            printf ($fh "%s","="); 
         } 
        printf($fh "\n");
   
        my $line = join("\t", @columns);
        printf($fh "%s\n", $line);
   
        $line = join("\t", @formats);
        printf($fh "%s\n", $line);
   
        foreach my $days (sort keys %$rdb_ref)
          {
           $number_of_mts++;
   
           # Join
           #
           my $line = join("\t", @{$report_ref->{$days}});
           printf($fh "%s\n", $line);
          }
        $fh->close;
       }
    }
        
  my $warn_message = "For site $cdwr_id found $number_of_mts records [ommitted $accounting_only]";
  $screen_logger->debug($warn_message);
     
  return $rdb_ref;
 
}

############################################################

    # This parser only looks at opening tags
    sub start { 
   foreach (@_) {
       print "===\nStart: $_\n";
    }
	my ($self, $tagname, $attr, $attrseq, $origtext) = @_;
	if ($tagname eq 'td') {
	    print "URL found: $origtext\n";
	}
    }

    # This parser only looks at opening tags
    sub end { 
   foreach (@_) {
       print "===\nStart: $_\n";
    }
	my ($self, $tagname, $attr, $attrseq, $origtext) = @_;
	if ($tagname eq 'td') {
	    print "URL found: $origtext\n";
	}
    }

############################################################

sub check_columns {
     
  $screen_logger->info("check_columns"); 
          
  my $Line       = shift;
  my $Wanted_Ref = shift;
  my $file_name  = shift;
     
  my $Field_Separator = ",";
         
  my @INPUT_COLUMNS  = ();
  my @WANTED_COLUMNS = @{$Wanted_Ref};
     
  # Parse columns
  #  
  @INPUT_COLUMNS = split(/$Field_Separator/,$Line);
                   
  # Check column names
  #
  my %SEEN_COLUMNS    = ();
  my @MISSING_COLUMNS = ();
  
  foreach my $column (@INPUT_COLUMNS) { $SEEN_COLUMNS{$column} = 1};
   
  foreach my $column (@WANTED_COLUMNS)
    {
     unless ($SEEN_COLUMNS{$column}) {
                
         # Missing a field
         #
         push(@MISSING_COLUMNS, $column);
        }
    }
  
  # Reset parsing delimiter
  #
  if(scalar(@MISSING_COLUMNS) > 0)
    {
     if($Field_Separator eq ",") {
        $Field_Separator = "\t";
     } else {
        $Field_Separator = ",";
     }
     @INPUT_COLUMNS = split(/$Field_Separator/,$Line);
    }
  my $message = "\nColumns \n\t" . join("\n\t",@INPUT_COLUMNS) . "\n\n";
  $screen_logger->debug($message);   
                   
  # Check column names
  #
  %SEEN_COLUMNS    = ();
  @MISSING_COLUMNS = ();
  
  foreach my $column (@INPUT_COLUMNS) { $SEEN_COLUMNS{$column} = 1};
   
  foreach my $column (@WANTED_COLUMNS)
    {
     unless ($SEEN_COLUMNS{$column}) {
                
         # Missing a field
         #
         push(@MISSING_COLUMNS, $column);
        }
    }
  
  # Check for missing column names
  #
  if(scalar(@MISSING_COLUMNS))
    {
     my $message = "Missing column(s) in $file_name file: \n\t" . join("\n\t", @MISSING_COLUMNS);
     $screen_logger->info($message); 
     exit;  
    }
   
  return $Field_Separator; 
}

############################################################

=item I<check_options>

 This INTERNAL subroutine is used to read and process the input options.

 Input:
   None

 Output:
   None

=cut

sub check_options {

   # Get the options from the command line
   #
   my $arg_ret = GetOptions  (
                              'help'               =>  \$help,
                              "usgs"               =>  \$usgs_file,
                              "owrd"               =>  \$owrd_file,
                              "cdwr"               =>  \$cdwr_file,
                              "all"                =>  \$all,
                              'debug'              =>  \$debug,
                              'quiet'              =>  \$quiet,
                              'logging'            =>  \$logging,
                              'report'             =>  \$report,
                             );

   # Invalid option
   #
   if(!$arg_ret) {
      my $die_message = "\n";
      $die_message   .= "\n use \n $FindBin::Script --help \n for complete list of options\n";
      die $die_message;
   }
    
  # Help
  # ------------------------------------------------------------------
  if(defined($help))
    {
     pod2usage(-verbose => 2);
    }

  # Check options
  # ------------------------------------------------------------------
  my $options_count = 0;

  $options_count++ if(defined($usgs_file));
  $options_count++ if(defined($owrd_file));
  $options_count++ if(defined($cdwr_file));
  $options_count++ if(defined($all));

  # Check options
  # ------------------------------------------------------------------
  if($options_count < 1)
    {
     my $die_message = '';
     $die_message   .= "    need to specify one or more --usgs, --owrd or --cdwr options\n";
     $die_message   .= "    use\n";
     $die_message   .= "    \t$FindBin::Script --usgs loads from NWIS records\n";
     $die_message   .= "    \t$FindBin::Script --owrd loads from OWRD records\n";
     $die_message   .= "    \t$FindBin::Script --cdwr loads from CDWR records\n";
     $die_message   .= "    \t$FindBin::Script --all loads from NWIS, OWRD, and CDWR records\n";
     die $die_message;
    }

  # Return
  # 
  return;

}

############################################################

=item I<init>

 This INTERNAL subroutine is used to initalize several variables.
 It sets the verbosity for screen logger, checks and sets the nwis_host,
 also sets the data type of the file to be processed.

 Input:
   None

 Output:
   None

=cut

sub init {
       
  # Check option --usgs 
  # --------------------------------------------
  if(defined($usgs_file))
    {
     $program_args .= "--usgs ";
    }
       
  # Check option --owrd 
  # --------------------------------------------
  if(defined($owrd_file))
    {
     $program_args .= "--owrd ";
    }
       
  # Check option --cdwr 
  # --------------------------------------------
  if(defined($cdwr_file))
    {
     $program_args .= "--cdwr ";
    }
       
  # Check option --all 
  # --------------------------------------------
  if(defined($all))
    {
     $usgs_file     = "on";
     $owrd_file     = "on";
     $cdwr_file     = "on";
     $program_args .= "--usgs ";
     $program_args .= "--owrd ";
     $program_args .= "--cdwr ";
    }

   # Quiet mode
   # ------------------------------------------
   $screen_logger->level($INFO);
   if(defined($quiet))
     {
      $screen_logger->less_logging(100);
      $program_args .= "--quiet ";
     }

   # Debug mode
   # ------------------------------------------
   if(defined($debug)) 
     {
      $screen_logger->level($DEBUG);
      $program_args .= "--debug ";
     }
   
  # Enable logging
  # ------------------------------------------
  if(defined($logging)) 
    {
     $program_args .= "--log ";
    }
       
  # Check option --report 
  # --------------------------------------------
  if(defined($report))
    {
     $program_args .= "--report ";
    }

  # Return
  # ------------------------------------------
  return;

}

############################################################

=item I<set_screen_logger>()

 This INTERNAL subroutine is used to set logger for the screen.

 Input:
      none

 Output:
      none

=cut

sub set_screen_logger {

   #  Log4perl
   #
   use Log::Log4perl;
   use Log::Log4perl::Layout;
   use Log::Log4perl::Level;
            
   # Define a file layout
   #
   my $layout          = Log::Log4perl::Layout::SimpleLayout->new("");
 
   # Define a file appender
   #
   $screen_logger      = get_logger("screen");
   my $screen_appender = Log::Log4perl::Appender->new(
                                                    "Log::Log4perl::Appender::Screen",
                                                    name      => "screen_logger"
                                                   );
         
   # Have both appenders use the same layout (could be different)
   #
   $screen_appender->layout($layout);
      
   $screen_logger->add_appender($screen_appender);
      
   $screen_logger->level($INFO);

   # Debug mode
   #
   if(defined($debug)) {
      $screen_logger->level($DEBUG);
   }

return $screen_logger;

}

############################################################

=item I<set_file_logger>()

 This INTERNAL subroutine is used to set loggers for
 a report

 Input:
      none

 Output:
      none

=cut

sub set_file_logger {

   #  Log4perl
   #
   use Log::Log4perl;
   use Log::Log4perl::Layout;
   use Log::Log4perl::Level;
            
   # Define a file layout
   #
   my $layout        = Log::Log4perl::Layout::PatternLayout->new(" %m%n");
   my $pid_layout    = Log::Log4perl::Layout::PatternLayout->new("%-5P %m%n");
             
   # Define LOGS directory
   #
   #my $LOGS          = File::Spec::Functions::catfile("/afs/.usgs.gov/www/or.water/htdocs/uo/internal_htmls/klamath_groundwater/waterlevels/obs_net/data/collection");
   my $LOGS          = "";

   # Define a file appender
   #
   $file_logger      = get_logger("file_logger");
      
   #my $file_log_file = File::Spec::Functions::catfile($LOGS,"prepare_gwlevels.log");
   my $file_log_file = "prepare_gwlevels.log";
   if(-e $file_log_file)
     {
      # Delete file
      #
      if(unlink($file_log_file) != 1) 
        {
         my $warn_message = "\n";
         $warn_message   .= " Unable to delete sitefile log file $file_log_file \n";
         $screen_logger->info($warn_message);
        }
     }
   my $file_appender = Log::Log4perl::Appender->new(
                                                    "Log::Log4perl::Appender::File",
                                                    name      => "file_logger",
                                                    filename  => $file_log_file
                                                   );
         
   # Have both appenders use the same layout (could be different)
   #
   $file_appender->layout($layout);
      
   $file_logger->add_appender($file_appender);
      
   $file_logger->level($INFO);

   # Debug mode
   #
   if(defined($debug)) {
      $file_logger->level($DEBUG);
   }

return;

}

############################################################

=item datetime2epoch(args)

 This INTERNAL subroutine generates a epoch timestamp in UTC milliseconds from 
 a date, time, and timezone.

 Input:
   $date                     -- date in yyyymmdd format
   $time                     -- date in hhmmss format
   $tz_cd                    -- time zone abbrevation code

 Output:
   $epoch_dt                 -- epoch timestamp in UTC milliseconds since Jan 1 1970

=cut

sub datetime2epoch 
 {
  my $date  = shift;
  my $time  = shift;
  my $tz_cd = shift;
            
  # -- Parse date and time
  #
  my ($year, $month, $day)     = $date =~ m/(\d{4})(\d{2})(\d{2})/;
    
  $month                     ||= 1;
  $day                       ||= 1;
                   
  my ($hour, $minute, $second) = $time =~ m/(\d{2})(\d{2})(\d{0,2})?/;
    
  $hour                      ||= 0;
  $minute                    ||= 0;
  $second                    ||= 0;
                   
  my $datetime = DateTime->new(
                               year      => $year,
                               month     => $month,
                               day       => $day,
                               hour      => $hour,
                               minute    => $minute,
                               time_zone => "UTC"
                              );
  my $epoch_dt = $datetime->epoch * 1000;

  # Time zone correction
  #
  my $time_zone_offset = 0;
  if(length($tz_cd) > 0)
    {
     my $offset_epoch_dt = tz_offset($tz_cd);
     if(length($offset_epoch_dt) > 0)
       {
        $time_zone_offset = $offset_epoch_dt * 1000;
       }
     #$epoch_dt -= $time_zone_offset;
    } 

  return $epoch_dt;
 }

############################################################

=item $integer = I<reformat_date_time(ARGS)>

 This INTERNAL subroutine to reformat the measurement date to the 
   mysql representation.

 Input:

  $date             -  Measurement date
  $time             -  Measurement time
  $lev_dt_acy_cd    -  NWIS date time accuracy code

 Output:
  lev_str_dt        - Date time string formatted to requested precision 

 Special Conditions:
   None

=cut

sub reformat_date_time {
  
  my ( $date, $time, $lev_dt_acy_cd ) = @_;
  
  my $lev_str_dt = "";
  
  # Reformat the date to the mysql representation
  #
  my ($day, $month, $year, $hour, $minute, $second);
  ($year,$month,$day)     = $date =~ m/^(\d{4,4})(\d{2,2})?(\d{2,2})?/;
  ($hour,$minute,$second) = $time =~ m/^(\d{2,2})(\d{2,2})?(\d{2,2})?/;
  $year                 ||= "0000";
  $month                ||= "00";
  $day                  ||= "00";
  $hour                 ||= "00";
  $minute               ||= "00";
  $second               ||= "00";
  
  # Reset date-time 
  #
  if($lev_dt_acy_cd eq "Y")
    {
     $lev_str_dt = sprintf("%04d",$year);
    }
  elsif($lev_dt_acy_cd eq "M")
    {
     $lev_str_dt = sprintf("%04d-%02d",$year,$month);
    }
  elsif($lev_dt_acy_cd eq "D")
    {
     $lev_str_dt = sprintf("%04d-%02d-%02d",$year,$month,$day);
    }
  elsif($lev_dt_acy_cd eq "h")
    {
     $lev_str_dt = sprintf("%04d-%02d-%02d %02d",$year,$month,$day,$hour);
    }
  elsif($lev_dt_acy_cd eq "m")
    {
     $lev_str_dt = sprintf("%04d-%02d-%02d %02d:%02d",$year,$month,$day,$hour,$minute);
    }
  elsif($lev_dt_acy_cd eq "s")
    {
     $lev_str_dt = sprintf("%04d-%02d-%02d %02d:%02d:%02d",$year,$month,$day,$hour,$minute,$second);
    }
         
  # Return date-time 
  #
  return $lev_str_dt;
}

############################################################

sub is_number {
    use POSIX qw(strtod);
    my $str = shift;
    $str =~ s/^\s+//;
    $str =~ s/\s+$//;
    $! = 0;
    my($num, $unparsed) = strtod($str);
    if (($str eq '') || ($unparsed != 0) || $!) {
        return;
    } else {
        return $num;
    } 
} 
