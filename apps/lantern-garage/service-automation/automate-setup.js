const BusinessAutomator = require('./business-automator');
const path = require('path');

/**
 * Master Automation Setup Script
 * Run this to initialize all business automation components
 */
async function runFullSetup() {
  console.log('🚀 Starting Lantern OS Business Automation Setup...\n');
  
  const repoRoot = path.resolve(__dirname, '../../..');
  const automator = new BusinessAutomator(repoRoot);
  
  try {
    // Step 1: Initialize directories
    console.log('📁 Initializing business directories...');
    const initResult = automator.initialize();
    console.log('✅ Directories initialized\n');
    
    // Step 2: Generate business plan
    console.log('📋 Generating business plan...');
    const businessPlanResult = automator.generateBusinessPlan();
    console.log('✅ Business plan generated:', businessPlanResult.path, '\n');
    
    // Step 3: Create email templates
    console.log('📧 Creating email templates...');
    const emailTemplatesResult = automator.createEmailTemplates();
    console.log('✅', emailTemplatesResult.count, 'email templates created:', emailTemplatesResult.path, '\n');
    
    // Step 4: Generate investor outreach targets
    console.log('🎯 Generating investor outreach targets...');
    const investorResult = automator.generateInvestorOutreach();
    console.log('✅', investorResult.count, 'investor targets identified:', investorResult.path, '\n');
    
    // Step 5: Create daily automation checklist
    console.log('✅ Creating daily automation checklist...');
    const checklistResult = automator.createDailyChecklist();
    console.log('✅', checklistResult.count, 'daily tasks defined:', checklistResult.path, '\n');
    
    // Step 6: Generate setup report
    console.log('📊 Generating comprehensive setup report...');
    const reportResult = automator.generateSetupReport();
    console.log('✅ Setup report generated:', reportResult.path, '\n');
    
    console.log('🎉 Business automation setup complete!\n');
    console.log('📋 Next Steps:');
    console.log('1. Review the setup report: ' + reportResult.path);
    console.log('2. Install payment bridge dependencies: cd apps/lantern-garage/payment-bridge && npm install');
    console.log('3. Configure payment bridge with your API keys');
    console.log('4. Review and complete manual actions from the report');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    process.exit(1);
  }
}

// Run the setup
if (require.main === module) {
  runFullSetup();
}

module.exports = { runFullSetup };